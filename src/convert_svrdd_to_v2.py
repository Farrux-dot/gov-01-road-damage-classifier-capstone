"""Convert audited SVRDD JSONL annotations into V2-ready annotations.

This converter reads source metadata and creates derived annotation files only.
It does not copy images, change raw files, create a final V2 split, or train a
model. Derived files belong in ignored data/processed/ storage.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

if __package__:
    from src.svrdd_v2_mapping import (
        SVRDD_CATEGORY_ID_TO_NAME,
        map_source_label,
        source_categories_to_multiclass,
        source_categories_to_multilabels,
    )
else:
    # Support the beginner-friendly documented command:
    # `python src/convert_svrdd_to_v2.py ...`.
    from svrdd_v2_mapping import (  # type: ignore[no-redef]
        SVRDD_CATEGORY_ID_TO_NAME,
        map_source_label,
        source_categories_to_multiclass,
        source_categories_to_multilabels,
    )


EXPECTED_SPLITS = ("train", "validation", "test")


def _require_object_lists(record: dict[str, Any]) -> tuple[list[Any], list[Any], list[Any], list[Any]]:
    """Return aligned source object fields or stop before making partial data."""
    objects = record.get("objects")
    if not isinstance(objects, dict):
        raise ValueError("record.objects must be an object")
    fields = ("bbox", "bbox_yolo", "categories", "category_names")
    values = tuple(objects.get(field) for field in fields)
    if not all(isinstance(value, list) for value in values):
        raise ValueError("record.objects must contain list fields: bbox, bbox_yolo, categories, category_names")
    if len({len(value) for value in values}) != 1:
        raise ValueError("source object fields have inconsistent lengths")
    if not values[0]:
        raise ValueError("SVRDD record has no objects and cannot receive a source-derived V2 class")
    return values  # type: ignore[return-value]


def convert_record(record: dict[str, Any]) -> dict[str, Any]:
    """Convert one valid SVRDD record without changing its box coordinates."""
    required_fields = ("file_name", "region", "image_id", "width", "height")
    missing_fields = [field for field in required_fields if field not in record]
    if missing_fields:
        raise ValueError(f"record missing required fields: {', '.join(missing_fields)}")

    boxes, yolo_boxes, category_ids, source_names = _require_object_lists(record)
    v2_labels: list[str] = []
    for category_id, source_name in zip(category_ids, source_names):
        expected_source_name = SVRDD_CATEGORY_ID_TO_NAME.get(category_id)
        if expected_source_name is None:
            raise ValueError(f"unsupported SVRDD category ID: {category_id!r}")
        if source_name != expected_source_name:
            raise ValueError(
                f"SVRDD category ID/name mismatch: {category_id!r} should be {expected_source_name!r}, got {source_name!r}"
            )
        v2_labels.append(map_source_label(source_name))

    return {
        "file_name": record["file_name"],
        "region": record["region"],
        "image_id": record["image_id"],
        "width": record["width"],
        "height": record["height"],
        "objects": {
            "bbox": boxes,
            "bbox_yolo": yolo_boxes,
            "source_category_ids": category_ids,
            "source_category_names": source_names,
            "v2_labels": v2_labels,
        },
        "multi_labels": source_categories_to_multilabels(source_names),
        "multi_class_label": source_categories_to_multiclass(source_names),
    }


def convert_metadata_file(input_path: Path, output_path: Path) -> dict[str, Any]:
    """Convert one JSONL split and return a summary without loading all records."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    object_counts: Counter[str] = Counter()
    image_counts: Counter[str] = Counter()
    record_count = 0
    with input_path.open(encoding="utf-8") as source, output_path.open("w", encoding="utf-8", newline="\n") as destination:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                source_record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON in {input_path.name} on line {line_number}") from error
            if not isinstance(source_record, dict):
                raise ValueError(f"Expected an object in {input_path.name} on line {line_number}")
            try:
                converted = convert_record(source_record)
            except ValueError as error:
                raise ValueError(f"{input_path.name} line {line_number}: {error}") from error
            destination.write(json.dumps(converted, ensure_ascii=False) + "\n")
            object_counts.update(converted["objects"]["v2_labels"])
            image_counts.update([converted["multi_class_label"]])
            record_count += 1
    return {
        "record_count": record_count,
        "object_counts_by_v2_label": dict(sorted(object_counts.items())),
        "image_counts_by_multiclass_label": dict(sorted(image_counts.items())),
        "output_file": output_path.name,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-dir", type=Path, required=True, help="Raw SVRDD folder containing <split>.metadata.jsonl files.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Ignored folder for V2-derived JSONL annotations.")
    parser.add_argument("--report", type=Path, required=True, help="Ignored JSON conversion-report path.")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "dataset": "SVRDD_YOLO",
        "mapping_version": "SVRDD seven source labels to four V2 conditions",
        "splits": {},
    }
    total_objects: Counter[str] = Counter()
    total_records = 0
    for split in EXPECTED_SPLITS:
        input_path = args.metadata_dir / f"{split}.metadata.jsonl"
        if not input_path.is_file():
            raise FileNotFoundError(f"Missing source metadata file: {input_path.name}")
        split_summary = convert_metadata_file(input_path, args.output_dir / f"{split}.v2.jsonl")
        report["splits"][split] = split_summary
        total_records += split_summary["record_count"]
        total_objects.update(split_summary["object_counts_by_v2_label"])

    report["total_record_count"] = total_records
    report["total_object_counts_by_v2_label"] = dict(sorted(total_objects.items()))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Converted {total_records} SVRDD records into {args.output_dir}")
    print(f"Saved conversion report: {args.report}")


if __name__ == "__main__":
    main()
