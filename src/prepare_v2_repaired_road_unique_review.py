"""Deduplicate repaired-road crops and prepare a focused quality review.

This tool keeps one record per exact crop checksum, writes a separate record
for redundant copies, and selects a deterministic region/size-balanced sample
from the unique source-labelled candidates. It does not delete crop files,
create final train/validation/test splits, or train a model.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageDraw


MATERIALIZED_COLUMNS = (
    "candidate_id",
    "class_label",
    "source_dataset",
    "source_split",
    "source_image_id",
    "split_group_id",
    "region",
    "source_image_path",
    "materialized_image_path",
    "target_box_xywh",
    "crop_box_xyxy",
    "target_box_in_crop_xywh",
    "crop_width",
    "crop_height",
    "training_status",
    "evidence_status",
    "output_sha256",
)
DEDUPLICATION_COLUMNS = MATERIALIZED_COLUMNS + (
    "deduplication_status",
    "duplicate_group_size",
    "kept_candidate_id",
    "deduplication_reason",
)
REVIEW_COLUMNS = (
    "sample_id",
    "size_band",
    "region",
    "crop_dimensions",
    "candidate_id",
    "source_image_id",
    "split_group_id",
    "materialized_image_path",
    "preview_image_path",
    "training_status",
    "evidence_status",
    "proposed_label",
    "human_decision",
    "reviewer_note",
)
HUMAN_APPROVED = "retain_human_approved_candidate"
AUDIT_SUPPORTED = "retain_source_labeled_audit_supported_candidate"
VALID_RETAINED_STATUSES = {HUMAN_APPROVED, AUDIT_SUPPORTED}
SIZE_BAND_ORDER = ("small_128_191", "medium_192_383", "large_384_plus")


def repository_relative(path: Path, repository_root: Path) -> str:
    """Return a portable repository-relative path and block outside paths."""
    try:
        return path.resolve().relative_to(repository_root.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(f"Path is outside the repository: {path}") from error


def resolve_repository_path(text: str, repository_root: Path) -> Path:
    """Resolve a manifest path without allowing escape from the repository."""
    path = (repository_root / Path(text)).resolve()
    repository_relative(path, repository_root)
    return path


def load_materialized_manifest(path: Path) -> list[dict[str, str]]:
    """Load and validate the crop materialization manifest."""
    with path.open(newline="", encoding="utf-8-sig") as source_file:
        reader = csv.DictReader(source_file)
        missing = [column for column in MATERIALIZED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path.name} is missing columns: {', '.join(missing)}")
        rows = [
            {column: (row.get(column) or "").strip() for column in MATERIALIZED_COLUMNS}
            for row in reader
        ]
    if not rows:
        raise ValueError("Materialized manifest contains no rows")
    candidate_counts = Counter(row["candidate_id"] for row in rows)
    duplicate_ids = sorted(candidate for candidate, count in candidate_counts.items() if count > 1)
    if duplicate_ids:
        raise ValueError(f"Duplicate candidate IDs: {', '.join(duplicate_ids)}")
    invalid_statuses = sorted(
        {row["training_status"] for row in rows if row["training_status"] not in VALID_RETAINED_STATUSES}
    )
    if invalid_statuses:
        raise ValueError(f"Unexpected training status(es): {', '.join(invalid_statuses)}")
    missing_hashes = [row["candidate_id"] for row in rows if len(row["output_sha256"]) != 64]
    if missing_hashes:
        raise ValueError(f"Missing or invalid crop checksum for {len(missing_hashes)} row(s)")
    return sorted(rows, key=lambda row: row["candidate_id"])


def _keeper_key(row: dict[str, str]) -> tuple[int, str]:
    """Prefer human-approved evidence, then use candidate ID for stability."""
    evidence_priority = 0 if row["training_status"] == HUMAN_APPROVED else 1
    return evidence_priority, row["candidate_id"]


def deduplicate_exact_crops(
    rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Return unique keepers and redundant exact copies without deleting files."""
    by_hash: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_hash[row["output_sha256"]].append(row)

    unique_rows: list[dict[str, str]] = []
    excluded_rows: list[dict[str, str]] = []
    for checksum in sorted(by_hash):
        group = sorted(by_hash[checksum], key=_keeper_key)
        split_groups = {row["split_group_id"] for row in group}
        source_images = {row["source_image_id"] for row in group}
        if len(split_groups) != 1 or len(source_images) != 1:
            raise ValueError(
                "Exact duplicate crop crosses a source-image split group; manual review is required"
            )
        keeper = group[0]
        group_size = str(len(group))
        unique_rows.append(
            {
                **keeper,
                "deduplication_status": "keep_unique_content",
                "duplicate_group_size": group_size,
                "kept_candidate_id": keeper["candidate_id"],
                "deduplication_reason": (
                    "only_crop_with_checksum"
                    if len(group) == 1
                    else "deterministic_keeper_for_exact_checksum"
                ),
            }
        )
        for redundant in group[1:]:
            excluded_rows.append(
                {
                    **redundant,
                    "deduplication_status": "exclude_exact_duplicate_content",
                    "duplicate_group_size": group_size,
                    "kept_candidate_id": keeper["candidate_id"],
                    "deduplication_reason": "same_output_sha256_as_kept_candidate",
                }
            )
    return (
        sorted(unique_rows, key=lambda row: row["candidate_id"]),
        sorted(excluded_rows, key=lambda row: row["candidate_id"]),
    )


def crop_size_band(row: dict[str, str]) -> str:
    """Assign one readable size band using the crop's shortest side."""
    side = min(int(row["crop_width"]), int(row["crop_height"]))
    if side < 128:
        raise ValueError(f"Crop is smaller than the documented 128-pixel minimum: {row['candidate_id']}")
    if side <= 191:
        return "small_128_191"
    if side <= 383:
        return "medium_192_383"
    return "large_384_plus"


def stable_rank(seed: int, candidate_id: str) -> str:
    """Create a repeatable pseudo-random ordering without mutable state."""
    return hashlib.sha256(f"{seed}:{candidate_id}".encode("utf-8")).hexdigest()


def select_quality_review(
    unique_rows: list[dict[str, str]], seed: int = 42, per_region_size: int = 4
) -> list[dict[str, str]]:
    """Select unreviewed unique crops across every region and size band."""
    candidates = [row for row in unique_rows if row["training_status"] == AUDIT_SUPPORTED]
    regions = sorted({row["region"] for row in candidates})
    if not regions:
        raise ValueError("No audit-supported unique candidates are available for quality review")

    selected: list[dict[str, str]] = []
    used_source_images: set[str] = set()
    sample_number = 1
    for size_band in SIZE_BAND_ORDER:
        for region in regions:
            stratum = [
                row
                for row in candidates
                if row["region"] == region and crop_size_band(row) == size_band
            ]
            stratum.sort(key=lambda row: (stable_rank(seed, row["candidate_id"]), row["candidate_id"]))
            chosen: list[dict[str, str]] = []
            for row in stratum:
                if row["source_image_id"] in used_source_images:
                    continue
                chosen.append(row)
                used_source_images.add(row["source_image_id"])
                if len(chosen) == per_region_size:
                    break
            if len(chosen) != per_region_size:
                raise ValueError(
                    f"Not enough unique source images for {region}/{size_band}: "
                    f"needed {per_region_size}, found {len(chosen)}"
                )
            for row in chosen:
                selected.append(
                    {
                        "sample_id": f"repaired_unique_{sample_number:03d}",
                        "size_band": size_band,
                        "region": region,
                        "crop_dimensions": f"{row['crop_width']}x{row['crop_height']}",
                        "candidate_id": row["candidate_id"],
                        "source_image_id": row["source_image_id"],
                        "split_group_id": row["split_group_id"],
                        "materialized_image_path": row["materialized_image_path"],
                        "preview_image_path": "",
                        "training_status": row["training_status"],
                        "evidence_status": row["evidence_status"],
                        "proposed_label": "repaired_road",
                        "human_decision": "pending",
                        "reviewer_note": "",
                    }
                )
                sample_number += 1
    return selected


def parse_xywh(text: str) -> tuple[float, float, float, float]:
    values = tuple(float(value.strip()) for value in text.split(","))
    if len(values) != 4:
        raise ValueError(f"Expected four box values, found: {text}")
    return values  # type: ignore[return-value]


def build_preview_images(
    review_rows: list[dict[str, str]],
    unique_by_candidate: dict[str, dict[str, str]],
    repository_root: Path,
    preview_dir: Path,
) -> None:
    """Create readable PNG previews with the intended repaired area boxed."""
    repository_relative(preview_dir, repository_root)
    preview_dir.mkdir(parents=True, exist_ok=True)
    expected_names = {f"{row['sample_id']}.png" for row in review_rows}
    unexpected = sorted({path.name for path in preview_dir.glob("*.png")} - expected_names)
    if unexpected:
        raise ValueError(
            f"Preview directory contains {len(unexpected)} unexpected PNG file(s); "
            "move them elsewhere before running this command"
        )

    for review in review_rows:
        source = unique_by_candidate[review["candidate_id"]]
        crop_path = resolve_repository_path(source["materialized_image_path"], repository_root)
        if not crop_path.is_file():
            raise FileNotFoundError(f"Missing materialized crop: {crop_path}")
        with Image.open(crop_path) as opened:
            image = opened.convert("RGB")
        x, y, width, height = parse_xywh(source["target_box_in_crop_xywh"])
        draw = ImageDraw.Draw(image)
        line_width = max(2, round(min(image.size) / 80))
        draw.rectangle((x, y, x + width, y + height), outline=(0, 255, 80), width=line_width)
        output_path = preview_dir / f"{review['sample_id']}.png"
        image.save(output_path, format="PNG", optimize=True)
        review["preview_image_path"] = repository_relative(output_path, repository_root)


def write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    """Write a deterministic UTF-8 CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def summarize(
    source_rows: list[dict[str, str]],
    unique_rows: list[dict[str, str]],
    excluded_rows: list[dict[str, str]],
    review_rows: list[dict[str, str]],
) -> dict[str, object]:
    return {
        "materialized_rows": len(source_rows),
        "unique_content_rows": len(unique_rows),
        "excluded_exact_duplicate_rows": len(excluded_rows),
        "review_rows": len(review_rows),
        "review_regions": dict(sorted(Counter(row["region"] for row in review_rows).items())),
        "review_size_bands": dict(
            sorted(Counter(row["size_band"] for row in review_rows).items())
        ),
        "review_unique_source_images": len({row["source_image_id"] for row in review_rows}),
        "files_deleted": 0,
        "final_split_created": False,
        "model_trained": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--materialized-manifest", type=Path, required=True)
    parser.add_argument("--unique-output", type=Path, required=True)
    parser.add_argument("--duplicates-output", type=Path, required=True)
    parser.add_argument("--review-output", type=Path, required=True)
    parser.add_argument("--preview-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--per-region-size", type=int, default=4)
    args = parser.parse_args()

    repository_root = args.repository_root.resolve()
    source_rows = load_materialized_manifest(args.materialized_manifest)
    unique_rows, excluded_rows = deduplicate_exact_crops(source_rows)
    review_rows = select_quality_review(unique_rows, args.seed, args.per_region_size)
    unique_by_candidate = {row["candidate_id"]: row for row in unique_rows}
    build_preview_images(review_rows, unique_by_candidate, repository_root, args.preview_dir.resolve())
    write_csv(args.unique_output, DEDUPLICATION_COLUMNS, unique_rows)
    write_csv(args.duplicates_output, DEDUPLICATION_COLUMNS, excluded_rows)
    write_csv(args.review_output, REVIEW_COLUMNS, review_rows)
    print(json.dumps(summarize(source_rows, unique_rows, excluded_rows, review_rows), indent=2))


if __name__ == "__main__":
    main()
