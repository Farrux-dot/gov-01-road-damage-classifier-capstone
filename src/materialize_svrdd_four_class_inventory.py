"""Create four traceable SVRDD object-crop inventories from source annotations.

This tool is deliberately a data-preparation step only.  It keeps the
source-provided train, validation, and test folders separate; it does not make
a new split, train a model, or decide whether a road condition is visually
correct.  It filters only objective technical problems and records every
accepted or rejected source object in the output manifest.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

if __package__:
    from src.materialize_v2_repaired_road_candidates import square_crop
    from src.svrdd_v2_mapping import SVRDD_CATEGORY_ID_TO_NAME, map_source_label
else:
    from materialize_v2_repaired_road_candidates import square_crop  # type: ignore[no-redef]
    from svrdd_v2_mapping import SVRDD_CATEGORY_ID_TO_NAME, map_source_label  # type: ignore[no-redef]


SOURCE_SPLITS = ("train", "validation", "test")
CLASS_NAMES = ("pothole", "crack", "manhole_cover", "repaired_road")
MANIFEST_COLUMNS = (
    "candidate_id", "class_label", "source_split", "source_image_id",
    "source_image_path", "source_category_name", "target_box_xywh",
    "target_min_side_px", "filter_decision", "filter_reason",
    "materialized_image_path", "output_sha256",
)


def repository_relative(path: Path, repository_root: Path) -> str:
    try:
        return path.resolve().relative_to(repository_root.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(f"Path is outside the repository: {path}") from error


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if line.strip():
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"Invalid JSON in {path.name} line {line_number}") from error
                if not isinstance(record, dict):
                    raise ValueError(f"Expected an object in {path.name} line {line_number}")
                records.append(record)
    return records


def parse_box(value: Any) -> tuple[float, float, float, float] | None:
    if not isinstance(value, list) or len(value) != 4:
        return None
    if not all(isinstance(item, (int, float)) and math.isfinite(item) for item in value):
        return None
    x, y, width, height = map(float, value)
    if x < 0 or y < 0 or width <= 0 or height <= 0:
        return None
    return x, y, width, height


def safe_file_name(candidate_id: str) -> str:
    return hashlib.sha256(candidate_id.encode("utf-8")).hexdigest()[:24] + ".jpg"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def make_row(**values: str) -> dict[str, str]:
    return {column: values.get(column, "") for column in MANIFEST_COLUMNS}


def materialize_split(
    records: list[dict[str, Any]], split: str, image_root: Path, output_root: Path,
    repository_root: Path, min_target_side: int,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen_hashes: dict[tuple[str, str], str] = {}
    for record in records:
        file_name = record.get("file_name")
        image_id = record.get("image_id")
        objects = record.get("objects")
        if not isinstance(file_name, str) or not isinstance(image_id, str) or not isinstance(objects, dict):
            raise ValueError(f"{split}: source metadata record is missing file_name, image_id, or objects")
        image_path = image_root / file_name
        categories = objects.get("categories")
        names = objects.get("category_names")
        boxes = objects.get("bbox")
        if not all(isinstance(value, list) for value in (categories, names, boxes)):
            raise ValueError(f"{split}/{file_name}: source object fields must be lists")
        if len({len(categories), len(names), len(boxes)}) != 1:
            raise ValueError(f"{split}/{file_name}: source object fields have inconsistent lengths")
        try:
            with Image.open(image_path) as opened:
                source = opened.convert("RGB")
        except (FileNotFoundError, UnidentifiedImageError, OSError):
            for index, category_name in enumerate(names):
                if isinstance(category_name, str) and category_name in SVRDD_CATEGORY_ID_TO_NAME.values():
                    class_name = map_source_label(category_name)
                    rows.append(make_row(
                        candidate_id=f"svrdd::{split}::{image_id}::{class_name}::{index:03d}",
                        class_label=class_name, source_split=split, source_image_id=image_id,
                        source_image_path=repository_relative(image_path, repository_root),
                        source_category_name=category_name, filter_decision="reject",
                        filter_reason="unreadable_or_missing_source_image",
                    ))
            continue
        for index, (category_id, category_name, box_value) in enumerate(zip(categories, names, boxes)):
            expected_name = SVRDD_CATEGORY_ID_TO_NAME.get(category_id)
            if expected_name is None or category_name != expected_name:
                raise ValueError(f"{split}/{file_name}#{index}: unsupported or inconsistent SVRDD category")
            class_name = map_source_label(category_name)
            candidate_id = f"svrdd::{split}::{image_id}::{class_name}::{index:03d}"
            box = parse_box(box_value)
            base = dict(
                candidate_id=candidate_id, class_label=class_name, source_split=split,
                source_image_id=image_id, source_image_path=repository_relative(image_path, repository_root),
                source_category_name=category_name,
            )
            if box is None or box[0] + box[2] > source.width + 0.01 or box[1] + box[3] > source.height + 0.01:
                rows.append(make_row(**base, filter_decision="reject", filter_reason="invalid_target_box"))
                continue
            min_side = min(box[2], box[3])
            box_text = ",".join(f"{value:.3f}" for value in box)
            base.update(target_box_xywh=box_text, target_min_side_px=f"{min_side:.3f}")
            if min_side < min_target_side:
                rows.append(make_row(**base, filter_decision="reject", filter_reason="target_box_smaller_than_minimum"))
                continue
            try:
                crop_box = square_crop(box, source.width, source.height)
            except ValueError:
                rows.append(
                    make_row(
                        **base,
                        filter_decision="reject",
                        filter_reason="context_crop_generation_error",
                    )
                )
                continue
            crop = source.crop(crop_box)
            class_dir = output_root / split / class_name
            class_dir.mkdir(parents=True, exist_ok=True)
            output_path = class_dir / safe_file_name(candidate_id)
            crop.save(output_path, format="JPEG", quality=95, subsampling=0, optimize=True)
            output_hash = sha256(output_path)
            hash_key = (split, class_name, output_hash)
            if hash_key in seen_hashes:
                output_path.unlink()
                rows.append(make_row(**base, filter_decision="reject", filter_reason=f"exact_duplicate_crop_of:{seen_hashes[hash_key]}"))
                continue
            seen_hashes[hash_key] = candidate_id
            rows.append(make_row(
                **base, filter_decision="retain", filter_reason="passed_technical_filters",
                materialized_image_path=repository_relative(output_path, repository_root), output_sha256=output_hash,
            ))
    return rows


def write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--metadata-dir", type=Path, required=True)
    parser.add_argument("--extracted-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--min-target-side", type=int, default=32)
    args = parser.parse_args()
    if args.min_target_side < 1:
        raise ValueError("--min-target-side must be at least 1 pixel")
    root = args.repository_root.resolve()
    output_root = args.output_dir.resolve()
    repository_relative(output_root, root)
    existing = list(output_root.rglob("*.jpg")) if output_root.exists() else []
    if existing:
        raise ValueError(f"Output folder is not empty ({len(existing)} JPEG files); choose a new folder")
    all_rows: list[dict[str, str]] = []
    for split in SOURCE_SPLITS:
        metadata_path = args.metadata_dir / f"{split}.metadata.jsonl"
        if not metadata_path.is_file():
            raise FileNotFoundError(f"Missing metadata: {metadata_path}")
        all_rows.extend(materialize_split(read_jsonl(metadata_path), split, args.extracted_dir / split, output_root, root, args.min_target_side))
    write_manifest(args.manifest, all_rows)
    retained = [row for row in all_rows if row["filter_decision"] == "retain"]
    report = {
        "dataset": "SVRDD_YOLO", "purpose": "four-class source-split-preserving inventory",
        "classes": list(CLASS_NAMES), "source_splits_kept_separate": True,
        "min_target_side_px": args.min_target_side, "rows_total": len(all_rows),
        "retained_by_split_and_class": {
            split: {label: sum(row["filter_decision"] == "retain" and row["source_split"] == split and row["class_label"] == label for row in all_rows) for label in CLASS_NAMES}
            for split in SOURCE_SPLITS
        },
        "rejected_by_reason": dict(sorted(Counter(row["filter_reason"] for row in all_rows if row["filter_decision"] == "reject").items())),
        "retained_total": len(retained), "final_v2_split_created": False, "model_trained": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
