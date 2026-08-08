"""Audit the Rome road-damage COCO dataset before creating a binary split."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, UnidentifiedImageError


def file_digest(path: Path) -> str:
    """Return the SHA-256 hash of one image file."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def capture_group(filename: str) -> tuple[str, str]:
    """Return a conservative date-based group inferred from the filename."""
    compact_match = re.match(r"^(\d{8})_", filename)
    if compact_match:
        return compact_match.group(1), "filename_capture_date"

    vlc_match = re.match(r"^vlcsnap-(\d{4})-(\d{2})-(\d{2})-", filename)
    if vlc_match:
        return "".join(vlc_match.groups()), "filename_capture_date"

    return "unknown_capture_group", "missing_capture_date"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    args = parser.parse_args()

    data_dir = args.data_dir
    images_dir = data_dir / "images"
    annotation_path = data_dir / "annotations_coco.json"
    if not images_dir.is_dir():
        raise FileNotFoundError(f"Image directory not found: {images_dir}")
    if not annotation_path.is_file():
        raise FileNotFoundError(f"COCO annotation file not found: {annotation_path}")

    coco = json.loads(annotation_path.read_text(encoding="utf-8"))
    required_keys = {"images", "annotations", "categories"}
    missing_keys = sorted(required_keys - set(coco))
    if missing_keys:
        raise ValueError(f"COCO file is missing keys: {missing_keys}")

    images = {image["id"]: image for image in coco["images"]}
    categories = {category["id"]: category["name"] for category in coco["categories"]}
    pothole_ids = {category_id for category_id, name in categories.items() if name.lower() == "pothole"}
    if not pothole_ids:
        raise ValueError("No category named 'pothole' was found.")

    annotations_by_image: dict[int, list[dict[str, object]]] = defaultdict(list)
    annotation_image_id_errors: list[int] = []
    for annotation in coco["annotations"]:
        image_id = annotation.get("image_id")
        if image_id not in images:
            annotation_image_id_errors.append(annotation.get("id", -1))
            continue
        annotations_by_image[image_id].append(annotation)

    jpg_paths = sorted(images_dir.glob("*.jpg"))
    image_paths = {path.name: path for path in jpg_paths}
    annotation_filenames = {image["file_name"] for image in images.values()}
    missing_image_files = sorted(annotation_filenames - set(image_paths))
    unlisted_jpg_files = sorted(set(image_paths) - annotation_filenames)

    unreadable_images: list[str] = []
    dimension_mismatches: list[dict[str, object]] = []
    hashes: dict[str, list[str]] = defaultdict(list)
    manifest_rows: list[dict[str, str]] = []
    binary_counts: Counter[str] = Counter()
    category_combination_counts: Counter[str] = Counter()
    group_counts: dict[str, Counter[str]] = defaultdict(Counter)
    nonpositive_boxes: list[dict[str, object]] = []
    out_of_frame_boxes: list[dict[str, object]] = []

    for image_id, image in sorted(images.items()):
        filename = image["file_name"]
        image_path = image_paths.get(filename)
        annotations = annotations_by_image[image_id]
        source_classes = sorted(
            {categories.get(annotation.get("category_id"), "unknown") for annotation in annotations}
        )
        binary_label = "Pothole" if any(annotation.get("category_id") in pothole_ids for annotation in annotations) else "No_pothole"
        group_id, group_source = capture_group(filename)
        binary_counts[binary_label] += 1
        category_combination_counts["|".join(source_classes) or "unannotated"] += 1
        group_counts[group_id][binary_label] += 1

        for annotation in annotations:
            bbox = annotation.get("bbox", [])
            issue_base = {
                "annotation_id": annotation.get("id"),
                "filename": filename,
                "category": categories.get(annotation.get("category_id"), "unknown"),
                "bbox": bbox,
            }
            if len(bbox) != 4:
                nonpositive_boxes.append({**issue_base, "reason": "bbox_does_not_have_four_values"})
                continue
            x, y, width, height = bbox
            if width <= 0 or height <= 0:
                nonpositive_boxes.append({**issue_base, "reason": "nonpositive_width_or_height"})
            if x < 0 or y < 0 or x + width > image["width"] or y + height > image["height"]:
                out_of_frame_boxes.append({**issue_base, "reason": "extends_outside_image"})

        if image_path is None:
            continue
        try:
            with Image.open(image_path) as opened_image:
                actual_width, actual_height = opened_image.size
                opened_image.verify()
        except (UnidentifiedImageError, OSError):
            unreadable_images.append(filename)
            continue
        if (actual_width, actual_height) != (image["width"], image["height"]):
            dimension_mismatches.append(
                {
                    "filename": filename,
                    "json_size": [image["width"], image["height"]],
                    "actual_size": [actual_width, actual_height],
                }
            )

        digest = file_digest(image_path)
        hashes[digest].append(filename)
        manifest_rows.append(
            {
                "source_filename": filename,
                "binary_label": binary_label,
                "source_classes": "|".join(source_classes),
                "annotation_count": str(len(annotations)),
                "label_source": "COCO pothole category presence",
                "group_id": group_id,
                "group_source": group_source,
                "sha256": digest,
            }
        )

    duplicate_groups = [sorted(filenames) for filenames in hashes.values() if len(filenames) > 1]
    report = {
        "data_dir": str(data_dir),
        "annotation_file": str(annotation_path),
        "provider_split_supplied": False,
        "image_records_in_json": len(images),
        "jpg_files_present": len(jpg_paths),
        "annotation_count": len(coco["annotations"]),
        "categories": categories,
        "binary_image_counts": dict(binary_counts),
        "image_category_combinations": dict(category_combination_counts),
        "group_counts": {group: dict(counts) for group, counts in sorted(group_counts.items())},
        "missing_image_files": missing_image_files,
        "unlisted_jpg_files": unlisted_jpg_files,
        "annotation_image_id_errors": annotation_image_id_errors,
        "unreadable_images": unreadable_images,
        "dimension_mismatches": dimension_mismatches,
        "nonpositive_boxes": nonpositive_boxes,
        "out_of_frame_boxes": out_of_frame_boxes,
        "exact_duplicate_groups": duplicate_groups,
        "warnings": [
            "No provider train/validation/test split is supplied.",
            "Capture groups are inferred from filename dates, not explicit video identifiers.",
            "The binary No_pothole class contains road images with cracks and/or manholes; it is not a clean-road class.",
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest_output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=tuple(manifest_rows[0]))
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
