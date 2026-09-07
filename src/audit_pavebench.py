"""Preflight audit for the downloaded PaveBench detection and classification data.

This reads raw PaveBench files only.  It does not create a V2 split, convert
labels, combine sources, or train a model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError


DETECTION_SPLITS = ("train", "val", "test")
EXPECTED_DETECTION_CATEGORIES = {
    1: "alligator",
    2: "crack",
    3: "patch",
    4: "pothole",
}
EXPECTED_CLASSIFICATION_CATEGORIES = {
    "alligator_crack",
    "longitudinal_crack",
    "negative",
    "patch",
    "pothole",
    "transverse_crack",
}


def file_digest(path: Path) -> str:
    """Return a SHA-256 digest while keeping memory use small."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_valid_coco_bbox(bbox: Any, width: int, height: int) -> bool:
    """Check a COCO [x, y, width, height] bounding box against its image."""
    if not isinstance(bbox, list) or len(bbox) != 4:
        return False
    if not all(isinstance(value, (int, float)) for value in bbox):
        return False
    x, y, box_width, box_height = bbox
    return (
        x >= 0
        and y >= 0
        and box_width > 0
        and box_height > 0
        and x + box_width <= width
        and y + box_height <= height
    )


def read_json(path: Path) -> dict[str, Any]:
    """Read one expected COCO JSON object."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="PaveBench data directory containing Distress_Classification and Distress_Detection.",
    )
    parser.add_argument("--output", type=Path, required=True, help="Ignored JSON audit-report path.")
    parser.add_argument(
        "--data-label",
        default="data/raw/v2/pavebench/data",
        help="Safe relative dataset label stored in the report instead of an absolute path.",
    )
    args = parser.parse_args()

    detection_root = args.data_dir / "Distress_Detection"
    classification_root = args.data_dir / "Distress_Classification"
    report: dict[str, Any] = {
        "dataset": "PaveBench",
        "data_label": args.data_label,
        "scope": "PaveBench classification and object-detection preflight only",
        "detection_expected_categories": {str(key): value for key, value in EXPECTED_DETECTION_CATEGORIES.items()},
        "detection_splits": {},
        "classification_source_categories": {},
        "exact_duplicate_group_count_across_detection_splits": 0,
        "exact_duplicate_examples_across_detection_splits": [],
        "warnings": [
            "PaveBench contains separate task copies. Do not combine its classification and detection folders without de-duplication.",
            "The classification label 'negative' is generic. It is not ground truth for Shadow, Puddle, Road_stain, Road_marking, Normal_asphalt, or Unpaved_road.",
            "This source is CC BY-NC-SA 4.0 according to its dataset card; retain the non-commercial and share-alike restriction in later V2 documentation.",
        ],
        "hard_errors": [],
    }
    hashes: dict[str, list[dict[str, str]]] = defaultdict(list)

    for split in DETECTION_SPLITS:
        annotation_path = detection_root / "annotations" / f"instances_{split}.json"
        image_root = detection_root / "images" / split
        if not annotation_path.is_file():
            report["hard_errors"].append(f"Missing annotation file: {annotation_path.name}")
            continue
        if not image_root.is_dir():
            report["hard_errors"].append(f"Missing detection image folder: {split}")
            continue

        payload = read_json(annotation_path)
        images = payload.get("images", [])
        annotations = payload.get("annotations", [])
        categories = payload.get("categories", [])
        if not all(isinstance(value, list) for value in (images, annotations, categories)):
            report["hard_errors"].append(f"{split}: COCO images, annotations, or categories is not a list")
            continue

        category_names = {
            category.get("id"): category.get("name")
            for category in categories
            if isinstance(category, dict)
        }
        if category_names != EXPECTED_DETECTION_CATEGORIES:
            report["hard_errors"].append(f"{split}: unexpected detection categories: {category_names}")

        paths_by_name = {path.name: path for path in image_root.glob("*.jpg")}
        images_by_id = {
            image.get("id"): image
            for image in images
            if isinstance(image, dict) and isinstance(image.get("id"), int)
        }
        image_names = {
            image.get("file_name")
            for image in images
            if isinstance(image, dict) and isinstance(image.get("file_name"), str)
        }
        missing_image_files = sorted(image_names - set(paths_by_name))
        unlisted_jpg_files = sorted(set(paths_by_name) - image_names)
        unreadable: list[str] = []
        dimension_mismatches: list[str] = []
        invalid_bboxes: list[str] = []
        invalid_annotation_image_ids: list[int] = []
        annotation_categories: Counter[str] = Counter()

        dimensions: dict[int, tuple[int, int]] = {}
        for image_id, image in images_by_id.items():
            file_name = image.get("file_name")
            if not isinstance(file_name, str) or file_name not in paths_by_name:
                continue
            image_path = paths_by_name[file_name]
            try:
                with Image.open(image_path) as opened:
                    opened.verify()
                with Image.open(image_path) as opened:
                    actual_size = opened.size
            except (UnidentifiedImageError, OSError):
                unreadable.append(file_name)
                continue
            dimensions[image_id] = actual_size
            if image.get("width") != actual_size[0] or image.get("height") != actual_size[1]:
                dimension_mismatches.append(file_name)
            hashes[file_digest(image_path)].append({"split": split, "path": file_name})

        for index, annotation in enumerate(annotations):
            if not isinstance(annotation, dict):
                invalid_annotation_image_ids.append(index)
                continue
            image_id = annotation.get("image_id")
            if image_id not in dimensions:
                invalid_annotation_image_ids.append(index)
                continue
            category_name = category_names.get(annotation.get("category_id"))
            if category_name is None:
                invalid_bboxes.append(f"annotation#{index}:unknown_category")
                continue
            annotation_categories[category_name] += 1
            width, height = dimensions[image_id]
            if not is_valid_coco_bbox(annotation.get("bbox"), width, height):
                invalid_bboxes.append(f"annotation#{index}")

        split_report = {
            "json_image_count": len(images),
            "jpg_file_count": len(paths_by_name),
            "annotation_count": len(annotations),
            "missing_image_file_count": len(missing_image_files),
            "unlisted_jpg_file_count": len(unlisted_jpg_files),
            "unreadable_image_count": len(unreadable),
            "dimension_mismatch_count": len(dimension_mismatches),
            "invalid_annotation_image_id_count": len(invalid_annotation_image_ids),
            "invalid_bbox_count": len(invalid_bboxes),
            "annotations_by_category": dict(sorted(annotation_categories.items())),
            "examples": {
                "missing_image_files": missing_image_files[:10],
                "unlisted_jpg_files": unlisted_jpg_files[:10],
                "unreadable_images": unreadable[:10],
                "dimension_mismatches": dimension_mismatches[:10],
                "invalid_bboxes": invalid_bboxes[:10],
            },
        }
        report["detection_splits"][split] = split_report
        for key in (
            "missing_image_file_count",
            "unlisted_jpg_file_count",
            "unreadable_image_count",
            "dimension_mismatch_count",
            "invalid_annotation_image_id_count",
            "invalid_bbox_count",
        ):
            if split_report[key]:
                report["hard_errors"].append(f"{split}: {key}={split_report[key]}")

    duplicate_groups = [
        entries
        for entries in hashes.values()
        if len({entry["split"] for entry in entries}) > 1
    ]
    report["exact_duplicate_group_count_across_detection_splits"] = len(duplicate_groups)
    report["exact_duplicate_examples_across_detection_splits"] = duplicate_groups[:25]
    if duplicate_groups:
        report["warnings"].append("Exact duplicate content exists across PaveBench detection splits.")

    if not classification_root.is_dir():
        report["hard_errors"].append("Missing PaveBench classification folder")
    else:
        class_counts: Counter[str] = Counter()
        unexpected_class_folders: set[str] = set()
        for image_path in classification_root.rglob("*.jpg"):
            category = image_path.parent.name
            class_counts[category] += 1
            if category not in EXPECTED_CLASSIFICATION_CATEGORIES:
                unexpected_class_folders.add(category)
        report["classification_source_categories"] = dict(sorted(class_counts.items()))
        report["classification_unexpected_category_folders"] = sorted(unexpected_class_folders)
        if unexpected_class_folders:
            report["hard_errors"].append(
                f"Unexpected classification folders: {sorted(unexpected_class_folders)}"
            )

    if report["hard_errors"]:
        report["audit_status"] = "failed"
    elif report["warnings"]:
        report["audit_status"] = "passed_with_warnings"
    else:
        report["audit_status"] = "passed"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["hard_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
