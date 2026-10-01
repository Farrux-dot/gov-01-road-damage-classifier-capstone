"""Build a safe, ignored multi-label candidate manifest from audited N-RDD2024 VOC labels.

The raw source is never changed.  The only coordinate repair allowed is clipping
an xmax/ymax value that is exactly one pixel past the image boundary.  N-RDD2024
labels crack, pothole, repaired crack, and manhole cover; the other active V2
conditions remain deliberately unknown.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


ACTIVE_CONDITIONS = (
    "crack",
    "pothole",
    "repaired_road",
    "manhole_cover",
    "unpaved_road",
    "road_marking",
    "speed_bump",
)
KNOWN_CONDITIONS = {"crack", "pothole", "repaired_road", "manhole_cover"}
SOURCE_TO_CONDITION = {
    "D00": "crack",
    "D10": "crack",
    "D20": "crack",
    "D30": "repaired_road",
    "D40": "pothole",
    "D70": "manhole_cover",
}


def _coverage_fields(present: set[str]) -> dict[str, int | str]:
    fields: dict[str, int | str] = {}
    for condition in ACTIVE_CONDITIONS:
        fields[f"{condition}_known"] = int(condition in KNOWN_CONDITIONS)
        fields[f"{condition}_present"] = int(condition in present) if condition in KNOWN_CONDITIONS else ""
    return fields


def _correct_box(box: ET.Element, width: float, height: float, source_path: Path) -> tuple[list[float], list[float], bool]:
    x1 = float(box.findtext("xmin", ""))
    y1 = float(box.findtext("ymin", ""))
    x2 = float(box.findtext("xmax", ""))
    y2 = float(box.findtext("ymax", ""))
    corrected_x2 = min(x2, width)
    corrected_y2 = min(y2, height)
    clipped = corrected_x2 != x2 or corrected_y2 != y2
    if clipped and (x2 - width > 1 or y2 - height > 1):
        raise ValueError(f"Unexpected boundary overflow in {source_path}")
    if not (0 <= x1 < corrected_x2 <= width and 0 <= y1 < corrected_y2 <= height):
        raise ValueError(f"Invalid corrected box in {source_path}")
    return [x1, y1, x2, y2], [x1, y1, corrected_x2, corrected_y2], clipped


def build_manifest(source_root: Path, manifest_path: Path, report_path: Path) -> dict[str, object]:
    records = 0
    mapped_object_counts: Counter[str] = Counter()
    clipped_object_counts: Counter[str] = Counter()
    source_object_counts: Counter[str] = Counter()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with manifest_path.open("w", encoding="utf-8", newline="\n") as destination:
        for annotation_path in sorted(source_root.rglob("*.xml")):
            image_path = annotation_path.with_suffix(".jpg")
            if not image_path.is_file():
                raise FileNotFoundError(f"Missing image for XML annotation: {annotation_path}")
            root = ET.parse(annotation_path).getroot()
            width = float(root.findtext("size/width", "0"))
            height = float(root.findtext("size/height", "0"))
            if width <= 0 or height <= 0:
                raise ValueError(f"Invalid image dimensions in {annotation_path}")

            present: set[str] = set()
            mapped_objects: list[dict[str, object]] = []
            source_labels: set[str] = set()
            for source_object in root.findall("object"):
                source_label = (source_object.findtext("name") or "").strip()
                source_labels.add(source_label)
                source_object_counts[source_label] += 1
                condition = SOURCE_TO_CONDITION.get(source_label)
                if condition is None:
                    continue
                box = source_object.find("bndbox")
                if box is None:
                    raise ValueError(f"Missing box in {annotation_path}")
                original_box, corrected_box, clipped = _correct_box(box, width, height, annotation_path)
                present.add(condition)
                mapped_object_counts[condition] += 1
                if clipped:
                    clipped_object_counts[condition] += 1
                mapped_objects.append(
                    {
                        "source_label": source_label,
                        "condition": condition,
                        "bbox_original": original_box,
                        "bbox_corrected": corrected_box,
                        "boundary_clipped": clipped,
                    }
                )

            relative_annotation = annotation_path.relative_to(source_root)
            split = next((part for part in relative_annotation.parts if part.lower() in {"train", "valid", "validation"}), "source_train_or_validation")
            stable_suffix = ":".join(relative_annotation.with_suffix("").parts)
            record = {
                "record_id": f"N_RDD2024:{stable_suffix}",
                "source_dataset": "N_RDD2024_official_Mendeley",
                "original_source_split": split,
                "stable_group_id": f"N_RDD2024:{stable_suffix}",
                "image_reference": str(image_path),
                "annotation_reference": str(annotation_path),
                "image_width": int(width),
                "image_height": int(height),
                "source_labels": sorted(source_labels),
                "mapped_objects": mapped_objects,
                **_coverage_fields(present),
            }
            destination.write(json.dumps(record, ensure_ascii=False) + "\n")
            records += 1

    summary: dict[str, object] = {
        "dataset": "N_RDD2024_official_Mendeley",
        "records": records,
        "known_conditions": sorted(KNOWN_CONDITIONS),
        "source_to_project_mapping": SOURCE_TO_CONDITION,
        "excluded_source_labels_from_project_mapping": ["D50", "D60", "D80", "D90"],
        "mapped_object_counts": dict(sorted(mapped_object_counts.items())),
        "all_source_object_counts": dict(sorted(source_object_counts.items())),
        "boundary_clipped_object_counts": dict(sorted(clipped_object_counts.items())),
        "total_boundary_clipped_objects": sum(clipped_object_counts.values()),
        "decision": "Derived candidate manifest only; raw XML labels were not modified. D80 patchy road is excluded because it is not automatically assumed to mean repaired road.",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True, help="Extracted N-RDD2024 VOC training/validation folders.")
    parser.add_argument("--manifest", type=Path, required=True, help="Ignored derived JSONL output path.")
    parser.add_argument("--report", type=Path, required=True, help="Ignored derived JSON report path.")
    args = parser.parse_args()
    summary = build_manifest(args.source_root, args.manifest, args.report)
    print(f"Built {summary['records']} N-RDD2024 candidate records.")
    print(f"Saved manifest: {args.manifest}")
    print(f"Saved report: {args.report}")


if __name__ == "__main__":
    main()
