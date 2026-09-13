"""Audit the ignored CeyMo training archive after extraction.

This tool reads source images and their XML, JSON, and PNG annotations. It
does not modify source labels, create a model split, or train a model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from src.ceymo_v2_mapping import CEYMO_LABEL_NAMES


POLYGON_BOUNDARY_TOLERANCE = 1.0


def file_digest(path: Path) -> str:
    """Return a SHA-256 digest without loading the whole file into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_valid_voc_bbox(
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    width: int,
    height: int,
) -> bool:
    """Return whether a Pascal VOC corner-format box is inside its image."""
    return 0 <= xmin < xmax <= width and 0 <= ymin < ymax <= height


def is_polygon_point_within_tolerance(
    x: float,
    y: float,
    width: int,
    height: int,
) -> bool:
    """Allow at most one pixel of source polygon boundary rounding."""
    return (
        -POLYGON_BOUNDARY_TOLERANCE <= x <= width + POLYGON_BOUNDARY_TOLERANCE
        and -POLYGON_BOUNDARY_TOLERANCE <= y <= height + POLYGON_BOUNDARY_TOLERANCE
    )


def read_image_size(path: Path) -> tuple[int, int]:
    """Verify an image and return its width and height."""
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        return image.size


def audit_ceymo(root: Path, data_label: str) -> dict[str, Any]:
    """Return a structural audit report for one extracted CeyMo folder."""
    folders = {
        "images": root / "images",
        "bbox_annotations": root / "bbox_annotations",
        "polygon_annotations": root / "polygon_annotations",
        "mask_annotations": root / "mask_annotations",
    }
    report: dict[str, Any] = {
        "dataset": "CeyMo",
        "data_label": data_label,
        "expected_source_labels": CEYMO_LABEL_NAMES,
        "hard_errors": [],
        "warnings": [],
    }

    missing_folders = [name for name, path in folders.items() if not path.is_dir()]
    if missing_folders:
        report["hard_errors"].append(
            "Missing required folders: " + ", ".join(sorted(missing_folders))
        )
        report["audit_status"] = "failed"
        return report

    images = sorted(folders["images"].glob("*.jpg"))
    xml_files = sorted(folders["bbox_annotations"].glob("*.xml"))
    json_files = sorted(folders["polygon_annotations"].glob("*.json"))
    mask_files = sorted(folders["mask_annotations"].glob("*.png"))
    files_by_type = {
        "images": images,
        "bbox_annotations": xml_files,
        "polygon_annotations": json_files,
        "mask_annotations": mask_files,
    }
    report["file_counts"] = {name: len(paths) for name, paths in files_by_type.items()}

    stems = {name: {path.stem for path in paths} for name, paths in files_by_type.items()}
    image_stems = stems["images"]
    report["counterpart_checks"] = {
        name: {
            "missing_for_images": len(image_stems - item_stems),
            "extra_without_images": len(item_stems - image_stems),
        }
        for name, item_stems in stems.items()
        if name != "images"
    }
    for name, result in report["counterpart_checks"].items():
        if result["missing_for_images"] or result["extra_without_images"]:
            report["hard_errors"].append(f"Filename mismatch for {name}")

    image_sizes: Counter[str] = Counter()
    mask_sizes: Counter[str] = Counter()
    unreadable_images: list[str] = []
    unreadable_masks: list[str] = []
    image_size_by_stem: dict[str, tuple[int, int]] = {}
    hashes: dict[str, list[str]] = defaultdict(list)

    for path in images:
        try:
            width, height = read_image_size(path)
            image_size_by_stem[path.stem] = (width, height)
            image_sizes[f"{width}x{height}"] += 1
        except (UnidentifiedImageError, OSError) as error:
            unreadable_images.append(f"{path.name}: {error}")
        hashes[file_digest(path)].append(path.name)

    for path in mask_files:
        try:
            width, height = read_image_size(path)
            mask_sizes[f"{width}x{height}"] += 1
            if image_size_by_stem.get(path.stem) != (width, height):
                report["hard_errors"].append(
                    f"Mask dimensions do not match image: {path.name}"
                )
        except (UnidentifiedImageError, OSError) as error:
            unreadable_masks.append(f"{path.name}: {error}")

    report["image_resolution_counts"] = dict(sorted(image_sizes.items()))
    report["mask_resolution_counts"] = dict(sorted(mask_sizes.items()))
    report["unreadable_image_count"] = len(unreadable_images)
    report["unreadable_mask_count"] = len(unreadable_masks)
    if unreadable_images or unreadable_masks:
        report["hard_errors"].append("One or more image or mask files are unreadable")

    xml_label_counts: Counter[str] = Counter()
    polygon_label_counts: Counter[str] = Counter()
    invalid_boxes: list[str] = []
    invalid_polygons: list[str] = []
    polygon_boundary_rounding: list[str] = []
    xml_errors: list[str] = []
    json_errors: list[str] = []
    json_image_path_mismatches: list[str] = []
    xml_labels_by_stem: dict[str, list[str]] = {}
    polygon_labels_by_stem: dict[str, list[str]] = {}

    for path in xml_files:
        try:
            annotation = ET.parse(path).getroot()
            filename = annotation.findtext("filename")
            width = int(annotation.findtext("size/width", "0"))
            height = int(annotation.findtext("size/height", "0"))
            if filename != f"{path.stem}.jpg":
                xml_errors.append(f"{path.name}: filename mismatch")
            if image_size_by_stem.get(path.stem) != (width, height):
                xml_errors.append(f"{path.name}: dimension mismatch")
            labels: list[str] = []
            for index, item in enumerate(annotation.findall("object")):
                label = (item.findtext("name") or "").strip()
                labels.append(label)
                xml_label_counts[label] += 1
                box = item.find("bndbox")
                if box is None:
                    invalid_boxes.append(f"{path.name}#{index}: missing bndbox")
                    continue
                try:
                    coordinates = [
                        float(box.findtext(name, "nan"))
                        for name in ("xmin", "ymin", "xmax", "ymax")
                    ]
                except ValueError:
                    invalid_boxes.append(f"{path.name}#{index}: non-numeric bndbox")
                    continue
                if not is_valid_voc_bbox(*coordinates, width, height):
                    invalid_boxes.append(f"{path.name}#{index}: outside image")
            xml_labels_by_stem[path.stem] = labels
        except (ET.ParseError, OSError, ValueError) as error:
            xml_errors.append(f"{path.name}: {error}")

    for path in json_files:
        try:
            annotation = json.loads(path.read_text(encoding="utf-8"))
            width = int(annotation.get("imageWidth", 0))
            height = int(annotation.get("imageHeight", 0))
            if annotation.get("imagePath") != f"{path.stem}.jpg":
                json_image_path_mismatches.append(
                    f"{path.name}: imagePath={annotation.get('imagePath')!r}"
                )
            if image_size_by_stem.get(path.stem) != (width, height):
                json_errors.append(f"{path.name}: dimension mismatch")
            labels: list[str] = []
            shapes = annotation.get("shapes")
            if not isinstance(shapes, list):
                raise ValueError("shapes is not a list")
            for index, shape in enumerate(shapes):
                label = shape.get("label")
                labels.append(label)
                polygon_label_counts[label] += 1
                points = shape.get("points")
                structurally_valid_points = (
                    isinstance(points, list)
                    and len(points) >= 3
                    and all(
                        isinstance(point, list)
                        and len(point) == 2
                        and all(isinstance(value, (int, float)) for value in point)
                        for point in points
                    )
                )
                points_within_tolerance = structurally_valid_points and all(
                    is_polygon_point_within_tolerance(
                        point[0], point[1], width, height
                    )
                    for point in points
                )
                points_strictly_inside = structurally_valid_points and all(
                    0 <= point[0] <= width and 0 <= point[1] <= height
                    for point in points
                )
                if shape.get("shape_type") != "polygon" or not points_within_tolerance:
                    invalid_polygons.append(f"{path.name}#{index}")
                elif not points_strictly_inside:
                    polygon_boundary_rounding.append(f"{path.name}#{index}")
            polygon_labels_by_stem[path.stem] = labels
        except (json.JSONDecodeError, OSError, TypeError, ValueError) as error:
            json_errors.append(f"{path.name}: {error}")

    unknown_xml_labels = sorted(set(xml_label_counts) - set(CEYMO_LABEL_NAMES))
    unknown_polygon_labels = sorted(set(polygon_label_counts) - set(CEYMO_LABEL_NAMES))
    label_mismatch_files = sorted(
        stem
        for stem in image_stems
        if Counter(xml_labels_by_stem.get(stem, []))
        != Counter(polygon_labels_by_stem.get(stem, []))
    )
    report["xml_object_count"] = sum(xml_label_counts.values())
    report["polygon_object_count"] = sum(polygon_label_counts.values())
    report["xml_labels"] = dict(sorted(xml_label_counts.items()))
    report["polygon_labels"] = dict(sorted(polygon_label_counts.items()))
    report["unknown_xml_labels"] = unknown_xml_labels
    report["unknown_polygon_labels"] = unknown_polygon_labels
    report["xml_polygon_label_mismatch_count"] = len(label_mismatch_files)
    report["invalid_bbox_count"] = len(invalid_boxes)
    report["invalid_polygon_count"] = len(invalid_polygons)
    report["polygon_boundary_rounding_count"] = len(polygon_boundary_rounding)
    report["xml_error_count"] = len(xml_errors)
    report["json_error_count"] = len(json_errors)
    report["json_image_path_mismatch_count"] = len(json_image_path_mismatches)

    if unknown_xml_labels or unknown_polygon_labels:
        report["hard_errors"].append("Unknown source annotation labels were found")
    if label_mismatch_files:
        report["hard_errors"].append("XML and polygon labels disagree for some images")
    if invalid_boxes or invalid_polygons or xml_errors or json_errors:
        report["hard_errors"].append("One or more source annotations are invalid")
    if polygon_boundary_rounding:
        report["warnings"].append(
            "One polygon uses less than one pixel of source boundary rounding; "
            "clip it during conversion without editing the raw annotation."
        )
    if json_image_path_mismatches:
        report["warnings"].append(
            "One polygon JSON imagePath value is inconsistent; pair annotations "
            "by verified file stem instead of trusting imagePath."
        )
    if xml_label_counts.get("BL") == 142 and xml_label_counts.get("CL") == 61:
        report["warnings"].append(
            "Observed BL/CL archive counts are reversed relative to the official "
            "paper's published train counts; do not rely on those two detailed "
            "subtypes until the discrepancy is resolved."
        )

    duplicate_groups = [names for names in hashes.values() if len(names) > 1]
    report["exact_duplicate_group_count"] = len(duplicate_groups)
    report["exact_duplicate_extra_file_count"] = sum(
        len(names) - 1 for names in duplicate_groups
    )
    report["exact_duplicate_groups"] = duplicate_groups
    if duplicate_groups:
        report["warnings"].append(
            "Exact duplicate images must be grouped or removed before creating V2 splits."
        )

    report["examples"] = {
        "unreadable_images": unreadable_images[:10],
        "unreadable_masks": unreadable_masks[:10],
        "invalid_boxes": invalid_boxes[:10],
        "invalid_polygons": invalid_polygons[:10],
        "polygon_boundary_rounding": polygon_boundary_rounding[:10],
        "xml_errors": xml_errors[:10],
        "json_errors": json_errors[:10],
        "json_image_path_mismatches": json_image_path_mismatches[:10],
        "xml_polygon_label_mismatches": label_mismatch_files[:10],
    }
    report["audit_status"] = (
        "failed"
        if report["hard_errors"]
        else "passed_with_warnings"
        if report["warnings"]
        else "passed"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--data-label",
        default="data/raw/v2/ceymo/train/extracted/train",
        help="Safe relative label stored instead of a local absolute path.",
    )
    args = parser.parse_args()

    report = audit_ceymo(args.data_dir, args.data_label)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["hard_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
