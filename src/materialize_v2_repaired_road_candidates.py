"""Materialize audited SVRDD repaired-road candidates as contextual crops.

This tool reads the retained-candidate manifest and source images, creates one
lossless-geometry JPEG crop per retained candidate, and writes a traceability
manifest. It does not resize crops, create final data splits, or train a model.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from PIL import Image


KEEP_COLUMNS = (
    "candidate_id",
    "source_dataset",
    "source_split",
    "source_image_id",
    "split_group_id",
    "region",
    "source_image_path",
    "target_box_xywh",
    "training_status",
    "evidence_status",
)
OUTPUT_COLUMNS = (
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
RETAINED_STATUSES = {
    "retain_human_approved_candidate",
    "retain_source_labeled_audit_supported_candidate",
}


def repository_relative(path: Path, repository_root: Path) -> str:
    """Return a portable repository-relative path and block outside paths."""
    try:
        return path.resolve().relative_to(repository_root.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(f"Path is outside the repository: {path}") from error


def resolve_repository_path(text: str, repository_root: Path) -> Path:
    """Resolve a manifest path while ensuring that it remains in the repository."""
    path = (repository_root / Path(text)).resolve()
    repository_relative(path, repository_root)
    return path


def load_keep_manifest(path: Path) -> list[dict[str, str]]:
    """Load and validate the retained-candidate manifest."""
    with path.open(newline="", encoding="utf-8-sig") as source_file:
        reader = csv.DictReader(source_file)
        missing = [column for column in KEEP_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path.name} is missing columns: {', '.join(missing)}")
        rows = [
            {column: (row.get(column) or "").strip() for column in KEEP_COLUMNS}
            for row in reader
        ]
    if not rows:
        raise ValueError("Retained-candidate manifest contains no rows")
    invalid_statuses = sorted(
        {row["training_status"] for row in rows if row["training_status"] not in RETAINED_STATUSES}
    )
    if invalid_statuses:
        raise ValueError(f"Manifest contains non-retained status(es): {', '.join(invalid_statuses)}")
    if {row["source_split"] for row in rows} != {"train"}:
        raise ValueError("Materialization is restricted to the audited SVRDD source-training split")
    candidate_counts = Counter(row["candidate_id"] for row in rows)
    duplicate_ids = sorted(key for key, count in candidate_counts.items() if count > 1)
    if duplicate_ids:
        raise ValueError(f"Duplicate candidate IDs: {', '.join(duplicate_ids)}")
    return sorted(rows, key=lambda row: row["candidate_id"])


def parse_xywh(text: str) -> tuple[float, float, float, float]:
    """Parse and validate an x,y,width,height box."""
    values = tuple(float(value.strip()) for value in text.split(","))
    if len(values) != 4:
        raise ValueError(f"Expected four box values, found: {text}")
    x, y, width, height = values
    if not all(math.isfinite(value) for value in values) or width <= 0 or height <= 0:
        raise ValueError(f"Invalid target box: {text}")
    return x, y, width, height


def square_crop(
    box: Iterable[float],
    image_width: int,
    image_height: int,
    context_factor: float = 2.5,
    minimum_side: int = 128,
) -> tuple[int, int, int, int]:
    """Create the contextual square used by the repaired-road audit."""
    x, y, width, height = map(float, box)
    if image_width <= 0 or image_height <= 0:
        raise ValueError("Image dimensions must be positive")
    if x < 0 or y < 0 or x + width > image_width + 0.01 or y + height > image_height + 0.01:
        raise ValueError(
            f"Target box {(x, y, width, height)} is outside image {image_width}x{image_height}"
        )
    side = min(
        max(int(round(max(width, height) * context_factor)), minimum_side),
        image_width,
        image_height,
    )
    center_x, center_y = x + width / 2, y + height / 2
    left = max(0, min(int(round(center_x - side / 2)), image_width - side))
    top = max(0, min(int(round(center_y - side / 2)), image_height - side))
    crop = left, top, left + side, top + side
    if x < crop[0] - 0.01 or y < crop[1] - 0.01 or x + width > crop[2] + 0.01 or y + height > crop[3] + 0.01:
        raise ValueError(f"Context crop does not contain the full target box: {box}")
    return crop


def safe_output_name(candidate_id: str) -> str:
    """Create a deterministic Windows-safe filename from a candidate ID."""
    digest = hashlib.sha256(candidate_id.encode("utf-8")).hexdigest()[:24]
    return f"repaired_road_{digest}.jpg"


def file_sha256(path: Path) -> str:
    """Return the SHA-256 checksum of one materialized crop."""
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def materialize(
    rows: list[dict[str, str]], repository_root: Path, output_dir: Path
) -> list[dict[str, str]]:
    """Create contextual crops and their traceability rows."""
    repository_relative(output_dir, repository_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    expected_names = {safe_output_name(row["candidate_id"]) for row in rows}
    existing_names = {path.name for path in output_dir.glob("*.jpg")}
    unexpected = sorted(existing_names - expected_names)
    if unexpected:
        raise ValueError(
            f"Output directory contains {len(unexpected)} unexpected JPEG file(s); "
            "move them elsewhere before running this command"
        )

    grouped: dict[Path, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        source_path = resolve_repository_path(row["source_image_path"], repository_root)
        if not source_path.is_file():
            raise FileNotFoundError(f"Missing source image: {source_path}")
        grouped[source_path].append(row)

    output_rows: list[dict[str, str]] = []
    for source_path in sorted(grouped, key=lambda path: path.as_posix()):
        with Image.open(source_path) as opened:
            source = opened.convert("RGB")
        for row in sorted(grouped[source_path], key=lambda value: value["candidate_id"]):
            target = parse_xywh(row["target_box_xywh"])
            crop_box = square_crop(target, source.width, source.height)
            crop = source.crop(crop_box)
            output_path = output_dir / safe_output_name(row["candidate_id"])
            crop.save(output_path, format="JPEG", quality=95, subsampling=0, optimize=True)
            target_in_crop = (
                target[0] - crop_box[0],
                target[1] - crop_box[1],
                target[2],
                target[3],
            )
            output_rows.append(
                {
                    "candidate_id": row["candidate_id"],
                    "class_label": "repaired_road",
                    "source_dataset": row["source_dataset"],
                    "source_split": row["source_split"],
                    "source_image_id": row["source_image_id"],
                    "split_group_id": row["split_group_id"],
                    "region": row["region"],
                    "source_image_path": row["source_image_path"],
                    "materialized_image_path": repository_relative(output_path, repository_root),
                    "target_box_xywh": row["target_box_xywh"],
                    "crop_box_xyxy": ",".join(str(value) for value in crop_box),
                    "target_box_in_crop_xywh": ",".join(f"{value:.3f}" for value in target_in_crop),
                    "crop_width": str(crop.width),
                    "crop_height": str(crop.height),
                    "training_status": row["training_status"],
                    "evidence_status": row["evidence_status"],
                    "output_sha256": file_sha256(output_path),
                }
            )

    actual_names = {path.name for path in output_dir.glob("*.jpg")}
    if actual_names != expected_names:
        raise RuntimeError("Materialized JPEG set does not exactly match the retained manifest")
    return sorted(output_rows, key=lambda row: row["candidate_id"])


def write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    """Write the deterministic crop traceability manifest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, str]]) -> dict[str, object]:
    """Return file, grouping, dimension, and exact-duplicate evidence."""
    hash_counts = Counter(row["output_sha256"] for row in rows)
    dimensions = Counter(f"{row['crop_width']}x{row['crop_height']}" for row in rows)
    return {
        "materialized_crops": len(rows),
        "unique_source_images": len({row["source_image_id"] for row in rows}),
        "unique_split_groups": len({row["split_group_id"] for row in rows}),
        "human_approved_crops": sum(
            row["training_status"] == "retain_human_approved_candidate" for row in rows
        ),
        "audit_supported_crops": sum(
            row["training_status"] == "retain_source_labeled_audit_supported_candidate"
            for row in rows
        ),
        "smallest_crop_side": min(int(row["crop_width"]) for row in rows),
        "largest_crop_side": max(int(row["crop_width"]) for row in rows),
        "dimension_count": len(dimensions),
        "exact_duplicate_hash_groups": sum(count > 1 for count in hash_counts.values()),
        "exact_duplicate_crops_beyond_first": sum(count - 1 for count in hash_counts.values()),
        "final_split_created": False,
        "model_trained": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--keep-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    args = parser.parse_args()

    repository_root = args.repository_root.resolve()
    rows = load_keep_manifest(args.keep_manifest)
    materialized = materialize(rows, repository_root, args.output_dir.resolve())
    write_manifest(args.output_manifest, materialized)
    print(json.dumps(summarize(materialized), indent=2))


if __name__ == "__main__":
    main()
