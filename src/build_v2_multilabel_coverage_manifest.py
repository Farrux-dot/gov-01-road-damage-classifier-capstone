"""Build a non-materialized V2 multi-label annotation-coverage manifest.

The manifest preserves a vital distinction: a source may confirm that a road
condition is absent, or it may simply not annotate that condition at all.
It does not copy images, create train/validation/test splits, or train a
model.
"""
from __future__ import annotations

import argparse
import csv
import json
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

if __package__:
    from src.svrdd_v2_mapping import source_categories_to_multilabels
else:
    from svrdd_v2_mapping import source_categories_to_multilabels  # type: ignore[no-redef]


ACTIVE_CONDITIONS = (
    "crack",
    "pothole",
    "repaired_road",
    "manhole_cover",
    "unpaved_road",
    "road_marking",
    "speed_bump",
)
SVRDD_KNOWN_CONDITIONS = {"crack", "pothole", "repaired_road", "manhole_cover"}
RTK_KNOWN_CONDITIONS = {
    "crack",
    "pothole",
    "repaired_road",
    "unpaved_road",
    "road_marking",
    "speed_bump",
}
RTK_LABEL_TO_CONDITION = {
    "craks": "crack",
    "pothole": "pothole",
    "patchs": "repaired_road",
    "roadUnpaved": "unpaved_road",
    "roadMarking": "road_marking",
    "speedBump": "speed_bump",
}
RTK_EXPECTED_SOURCE_LABELS = {
    "roadAsphalt",
    "roadUnpaved",
    "roadPaved",
    "roadMarking",
    "craks",
    "catsEye",
    "stormDrain",
    "patchs",
    "waterPuddle",
    "pothole",
    "speedBump",
}


def _coverage_fields(present: set[str], known: set[str]) -> dict[str, int | str]:
    """Return stable present/known columns for one source record.

    A present value is blank when the source does not know that condition.
    This prevents an unknown label from being silently converted into no.
    """
    fields: dict[str, int | str] = {}
    for condition in ACTIVE_CONDITIONS:
        fields[f"{condition}_known"] = int(condition in known)
        fields[f"{condition}_present"] = int(condition in present) if condition in known else ""
    return fields


def _svrdd_rows(metadata_path: Path, images_root: Path) -> list[dict[str, Any]]:
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Missing SVRDD metadata: {metadata_path}")
    rows: list[dict[str, Any]] = []
    with metadata_path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            file_name = record.get("file_name")
            image_id = record.get("image_id")
            objects = record.get("objects")
            if not isinstance(file_name, str) or not isinstance(image_id, str) or not isinstance(objects, dict):
                raise ValueError(f"Invalid SVRDD record on line {line_number}")
            source_names = objects.get("category_names")
            if not isinstance(source_names, list) or not all(isinstance(name, str) for name in source_names):
                raise ValueError(f"SVRDD line {line_number} has invalid source category names")
            image_path = images_root / file_name
            if not image_path.is_file():
                raise FileNotFoundError(f"SVRDD image missing for line {line_number}: {image_path}")
            labels = source_categories_to_multilabels(source_names)
            present = {condition for condition in SVRDD_KNOWN_CONDITIONS if labels[f"{condition}_present"]}
            rows.append(
                {
                    "record_id": f"SVRDD_YOLO:train:{image_id}",
                    "source_dataset": "SVRDD_YOLO",
                    "original_source_split": "train",
                    "stable_group_id": f"SVRDD_YOLO:{image_id}",
                    "image_reference": str(image_path),
                    "annotation_reference": f"{metadata_path}#line={line_number}",
                    **_coverage_fields(present, SVRDD_KNOWN_CONDITIONS),
                }
            )
    return rows


def _zip_files(archive: zipfile.ZipFile, suffix: str) -> dict[str, str]:
    """Return archive members indexed by stem, stopping on ambiguous names."""
    result: dict[str, str] = {}
    for member in archive.namelist():
        if member.endswith("/") or Path(member).suffix.lower() != suffix:
            continue
        stem = Path(member).stem
        if stem in result:
            raise ValueError(f"Duplicate RTK archive member stem: {stem}")
        result[stem] = member
    return result


def _rtk_rows(images_archive_path: Path, annotations_archive_path: Path) -> list[dict[str, Any]]:
    if not images_archive_path.is_file() or not annotations_archive_path.is_file():
        raise FileNotFoundError("RTK original-frame and JSON annotation archives are both required")
    rows: list[dict[str, Any]] = []
    with zipfile.ZipFile(images_archive_path) as images_archive, zipfile.ZipFile(annotations_archive_path) as annotations_archive:
        image_members = _zip_files(images_archive, ".png")
        annotation_members = _zip_files(annotations_archive, ".json")
        if set(image_members) != set(annotation_members):
            raise ValueError("RTK original-frame and JSON annotation archive members do not match")
        if len(image_members) != 701:
            raise ValueError(f"Expected 701 RTK records, found {len(image_members)}")
        for stem in sorted(image_members):
            annotation_member = annotation_members[stem]
            annotation = json.loads(annotations_archive.read(annotation_member).decode("utf-8"))
            shapes = annotation.get("shapes")
            if not isinstance(shapes, list):
                raise ValueError(f"RTK annotation has no shapes list: {annotation_member}")
            source_labels: set[str] = set()
            for shape in shapes:
                if not isinstance(shape, dict) or not isinstance(shape.get("label"), str):
                    raise ValueError(f"RTK annotation has an invalid shape: {annotation_member}")
                source_labels.add(shape["label"])
            unknown_labels = source_labels - RTK_EXPECTED_SOURCE_LABELS
            if unknown_labels:
                raise ValueError(f"RTK annotation has unexpected labels in {annotation_member}: {sorted(unknown_labels)}")
            present = {RTK_LABEL_TO_CONDITION[label] for label in source_labels if label in RTK_LABEL_TO_CONDITION}
            rows.append(
                {
                    "record_id": f"RTK_SEMANTIC_SEGMENTATION:{stem}",
                    "source_dataset": "RTK_SEMANTIC_SEGMENTATION",
                    "original_source_split": "unsplit",
                    "stable_group_id": f"RTK_SEMANTIC_SEGMENTATION:{stem}",
                    "image_reference": f"{images_archive_path}#{image_members[stem]}",
                    "annotation_reference": f"{annotations_archive_path}#{annotation_member}",
                    **_coverage_fields(present, RTK_KNOWN_CONDITIONS),
                }
            )
    return rows


def _fieldnames() -> list[str]:
    fields = [
        "record_id",
        "source_dataset",
        "original_source_split",
        "stable_group_id",
        "image_reference",
        "annotation_reference",
    ]
    for condition in ACTIVE_CONDITIONS:
        fields.extend((f"{condition}_known", f"{condition}_present"))
    return fields


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_source: dict[str, Any] = {}
    for source_name in sorted({str(row["source_dataset"]) for row in rows}):
        source_rows = [row for row in rows if row["source_dataset"] == source_name]
        coverage: dict[str, dict[str, int]] = {}
        for condition in ACTIVE_CONDITIONS:
            coverage[condition] = {
                "known_records": sum(row[f"{condition}_known"] == 1 for row in source_rows),
                "positive_records": sum(row[f"{condition}_present"] == 1 for row in source_rows),
            }
        by_source[source_name] = {"records": len(source_rows), "coverage": coverage}
    return {"total_records": len(rows), "sources": by_source}


def build_manifest(
    *,
    svrdd_metadata: Path,
    svrdd_images_root: Path,
    rtk_images_archive: Path,
    rtk_annotations_archive: Path,
    output_csv: Path,
    summary_json: Path,
) -> dict[str, Any]:
    """Build and save the coverage manifest plus a compact verification summary."""
    rows = _svrdd_rows(svrdd_metadata, svrdd_images_root) + _rtk_rows(rtk_images_archive, rtk_annotations_archive)
    ids = [str(row["record_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Manifest record IDs must be unique")
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=_fieldnames())
        writer.writeheader()
        writer.writerows(rows)
    result = _summary(rows)
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--svrdd-metadata", type=Path, required=True)
    parser.add_argument("--svrdd-images-root", type=Path, required=True)
    parser.add_argument("--rtk-images-archive", type=Path, required=True)
    parser.add_argument("--rtk-annotations-archive", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True, help="Ignored coverage-manifest output path")
    parser.add_argument("--summary-json", type=Path, required=True, help="Ignored verification-summary output path")
    args = parser.parse_args()
    result = build_manifest(
        svrdd_metadata=args.svrdd_metadata,
        svrdd_images_root=args.svrdd_images_root,
        rtk_images_archive=args.rtk_images_archive,
        rtk_annotations_archive=args.rtk_annotations_archive,
        output_csv=args.output_csv,
        summary_json=args.summary_json,
    )
    print(f"Built {result['total_records']} non-materialized coverage records: {args.output_csv}")
    for source_name, source_summary in result["sources"].items():
        print(f"- {source_name}: {source_summary['records']} records")


if __name__ == "__main__":
    main()
