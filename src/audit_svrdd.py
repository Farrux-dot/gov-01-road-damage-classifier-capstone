"""Audit the raw SVRDD image archives and their matching JSONL annotations.

This tool only reads raw V2 data. It does not create a training split, train a
model, or change the V1 project data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError


EXPECTED_SPLITS = ("train", "validation", "test")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
CATEGORY_NAMES = {
    0: "longitudinal crack",
    1: "transverse crack",
    2: "alligator crack",
    3: "pothole",
    4: "manhole cover",
    5: "longitudinal patch",
    6: "transverse patch",
}
BOUNDARY_TOLERANCE = 0.01


def file_digest(path: Path) -> str:
    """Return a SHA-256 digest without loading the entire image into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if line.strip():
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"Invalid JSON in {path} on line {line_number}") from error
                if not isinstance(record, dict):
                    raise ValueError(f"Expected an object in {path} on line {line_number}")
                records.append(record)
    return records


def is_valid_bbox(bbox: Any, width: int, height: int) -> bool:
    """Check an absolute [x, y, width, height] bounding box."""
    if not isinstance(bbox, list) or len(bbox) != 4:
        return False
    if not all(isinstance(value, (int, float)) for value in bbox):
        return False
    x, y, box_width, box_height = bbox
    # The supplied source sometimes represents an edge as 1024.001 instead of
    # 1024.0. Allow only this tiny floating-point rounding difference.
    return (
        x >= 0
        and y >= 0
        and box_width > 0
        and box_height > 0
        and x + box_width <= width + BOUNDARY_TOLERANCE
        and y + box_height <= height + BOUNDARY_TOLERANCE
    )


def is_valid_yolo_bbox(bbox: Any) -> bool:
    """Check a normalized YOLO [x_center, y_center, width, height] box."""
    if not isinstance(bbox, list) or len(bbox) != 4:
        return False
    if not all(isinstance(value, (int, float)) for value in bbox):
        return False
    x_center, y_center, box_width, box_height = bbox
    return 0 <= x_center <= 1 and 0 <= y_center <= 1 and 0 < box_width <= 1 and 0 < box_height <= 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extracted-dir", type=Path, required=True, help="Folder containing train, validation, and test image folders.")
    parser.add_argument("--metadata-dir", type=Path, required=True, help="Folder containing <split>.metadata.jsonl files.")
    parser.add_argument("--output", type=Path, required=True, help="JSON audit-report path.")
    parser.add_argument("--data-label", default="data/raw/v2/svrdd", help="Safe relative label shown in the report instead of a local absolute path.")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "dataset": "SVRDD_YOLO",
        "data_label": args.data_label,
        "expected_splits": list(EXPECTED_SPLITS),
        "category_names": {str(key): value for key, value in CATEGORY_NAMES.items()},
        "splits": {},
        "exact_duplicate_groups_across_splits": [],
        "warnings": [],
        "hard_errors": [],
    }
    hashes: dict[str, list[dict[str, str]]] = defaultdict(list)
    image_ids: dict[str, list[str]] = defaultdict(list)
    all_category_counts: Counter[str] = Counter()

    for split in EXPECTED_SPLITS:
        image_root = args.extracted_dir / split
        metadata_path = args.metadata_dir / f"{split}.metadata.jsonl"
        if not image_root.is_dir():
            report["hard_errors"].append(f"Missing extracted image folder: {split}")
            continue
        if not metadata_path.is_file():
            report["hard_errors"].append(f"Missing metadata file: {split}.metadata.jsonl")
            continue

        records = read_jsonl(metadata_path)
        images = {
            path.relative_to(image_root).as_posix(): path
            for path in image_root.rglob("*")
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        }
        records_by_file: dict[str, dict[str, Any]] = {}
        repeated_record_paths: list[str] = []
        for record in records:
            file_name = record.get("file_name")
            if not isinstance(file_name, str):
                report["hard_errors"].append(f"{split}: a metadata record has no string file_name")
                continue
            if file_name in records_by_file:
                repeated_record_paths.append(file_name)
            records_by_file[file_name] = record

        image_paths = set(images)
        record_paths = set(records_by_file)
        missing_metadata = sorted(image_paths - record_paths)
        missing_images = sorted(record_paths - image_paths)
        unreadable: list[str] = []
        dimension_mismatches: list[str] = []
        invalid_absolute_boxes: list[str] = []
        invalid_yolo_boxes: list[str] = []
        invalid_categories: list[str] = []
        invalid_category_names: list[str] = []
        inconsistent_object_lengths: list[str] = []
        category_counts: Counter[str] = Counter()
        zero_annotation_images = 0
        region_counts: Counter[str] = Counter()

        for relative_path, image_path in images.items():
            record = records_by_file.get(relative_path)
            if record is None:
                continue
            try:
                with Image.open(image_path) as image:
                    image.verify()
                with Image.open(image_path) as image:
                    width, height = image.size
            except (UnidentifiedImageError, OSError):
                unreadable.append(relative_path)
                continue

            if record.get("width") != width or record.get("height") != height:
                dimension_mismatches.append(relative_path)
            region = record.get("region")
            if isinstance(region, str):
                region_counts[region] += 1
            image_id = record.get("image_id")
            if isinstance(image_id, str):
                image_ids[image_id].append(f"{split}/{relative_path}")

            objects = record.get("objects")
            if not isinstance(objects, dict):
                inconsistent_object_lengths.append(relative_path)
            else:
                absolute_boxes = objects.get("bbox", [])
                yolo_boxes = objects.get("bbox_yolo", [])
                categories = objects.get("categories", [])
                category_names = objects.get("category_names", [])
                object_lengths = [len(value) for value in (absolute_boxes, yolo_boxes, categories, category_names) if isinstance(value, list)]
                if len(object_lengths) != 4 or len(set(object_lengths)) != 1:
                    inconsistent_object_lengths.append(relative_path)
                elif not object_lengths[0]:
                    zero_annotation_images += 1
                else:
                    for index, (absolute_box, yolo_box, category, category_name) in enumerate(zip(absolute_boxes, yolo_boxes, categories, category_names)):
                        item = f"{relative_path}#{index}"
                        if not is_valid_bbox(absolute_box, width, height):
                            invalid_absolute_boxes.append(item)
                        if not is_valid_yolo_bbox(yolo_box):
                            invalid_yolo_boxes.append(item)
                        if category not in CATEGORY_NAMES:
                            invalid_categories.append(item)
                        else:
                            expected_name = CATEGORY_NAMES[category]
                            category_counts[expected_name] += 1
                            all_category_counts[expected_name] += 1
                            if category_name != expected_name:
                                invalid_category_names.append(item)

            hashes[file_digest(image_path)].append({"split": split, "path": relative_path})

        split_report = {
            "image_count": len(images),
            "metadata_record_count": len(records),
            "missing_metadata_count": len(missing_metadata),
            "missing_image_count": len(missing_images),
            "repeated_metadata_path_count": len(repeated_record_paths),
            "unreadable_image_count": len(unreadable),
            "dimension_mismatch_count": len(dimension_mismatches),
            "inconsistent_object_length_count": len(inconsistent_object_lengths),
            "invalid_absolute_bbox_count": len(invalid_absolute_boxes),
            "invalid_yolo_bbox_count": len(invalid_yolo_boxes),
            "invalid_category_count": len(invalid_categories),
            "invalid_category_name_count": len(invalid_category_names),
            "zero_annotation_image_count": zero_annotation_images,
            "annotations_by_category": dict(sorted(category_counts.items())),
            "images_by_region": dict(sorted(region_counts.items())),
            "examples": {
                "missing_metadata": missing_metadata[:10],
                "missing_images": missing_images[:10],
                "unreadable": unreadable[:10],
                "dimension_mismatches": dimension_mismatches[:10],
                "invalid_absolute_boxes": invalid_absolute_boxes[:10],
                "invalid_yolo_boxes": invalid_yolo_boxes[:10],
                "invalid_categories": invalid_categories[:10],
            },
        }
        report["splits"][split] = split_report

        for key in (
            "missing_metadata_count",
            "missing_image_count",
            "repeated_metadata_path_count",
            "unreadable_image_count",
            "dimension_mismatch_count",
            "inconsistent_object_length_count",
            "invalid_absolute_bbox_count",
            "invalid_yolo_bbox_count",
            "invalid_category_count",
            "invalid_category_name_count",
        ):
            if split_report[key]:
                report["hard_errors"].append(f"{split}: {key}={split_report[key]}")

    duplicate_groups = [items for items in hashes.values() if len({item["split"] for item in items}) > 1]
    report["exact_duplicate_group_count_across_splits"] = len(duplicate_groups)
    report["exact_duplicate_groups_across_splits"] = duplicate_groups[:25]
    if duplicate_groups:
        report["warnings"].append("Exact duplicate image content exists across source-provided splits.")

    repeated_image_ids = [paths for paths in image_ids.values() if len(paths) > 1]
    report["repeated_image_id_group_count"] = len(repeated_image_ids)
    report["repeated_image_id_examples"] = repeated_image_ids[:25]
    if repeated_image_ids:
        report["warnings"].append("Some source image_id values appear more than once; inspect grouping before a new V2 split.")

    report["annotations_by_category_total"] = dict(sorted(all_category_counts.items()))
    report["audit_status"] = "needs_review" if report["hard_errors"] or report["warnings"] else "passed"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["hard_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
