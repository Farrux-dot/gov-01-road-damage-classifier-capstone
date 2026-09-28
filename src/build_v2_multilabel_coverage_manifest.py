"""Build a non-materialized V2 multi-label annotation-coverage manifest.

The manifest preserves a vital distinction: a source may confirm that a road
condition is absent, or it may simply not annotate that condition at all.
It does not copy images, create train/validation/test splits, or train a
model.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import zipfile
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


def _speed_bump_partial_row(
    *,
    record_id: str,
    source_dataset: str,
    image_reference: str,
    annotation_reference: str,
) -> dict[str, Any]:
    """Create a row for a source that verifies only a speed bump is present."""
    return {
        "record_id": record_id,
        "source_dataset": source_dataset,
        "original_source_split": "train",
        "stable_group_id": record_id,
        "image_reference": image_reference,
        "annotation_reference": annotation_reference,
        **_coverage_fields({"speed_bump"}, {"speed_bump"}),
    }


def _kaggle_speed_bump_rows(audit_path: Path, project_root: Path) -> tuple[list[dict[str, Any]], set[str]]:
    """Reuse only the later audited, non-sequence Kaggle speed-bump candidates."""
    if not audit_path.is_file():
        raise FileNotFoundError(f"Missing Kaggle speed-bump audit: {audit_path}")
    rows: list[dict[str, Any]] = []
    hashes: set[str] = set()
    with audit_path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        required = {"source_record_id", "relative_image_path", "sha256", "decision"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError("Kaggle speed-bump audit has an unexpected schema")
        for line_number, record in enumerate(reader, start=2):
            if record["decision"] != "keep_train_speed_bump_candidate":
                continue
            record_id = record["source_record_id"]
            image_relative_path = record["relative_image_path"]
            image_path = project_root / image_relative_path
            source_hash = record["sha256"]
            if not record_id or not image_relative_path or not source_hash:
                raise ValueError(f"Kaggle speed-bump audit line {line_number} is incomplete")
            if not image_path.is_file():
                raise FileNotFoundError(f"Kaggle speed-bump image missing: {image_path}")
            if source_hash in hashes:
                raise ValueError(f"Kaggle audit retained an exact duplicate: {record_id}")
            hashes.add(source_hash)
            rows.append(
                _speed_bump_partial_row(
                    record_id=f"KAGGLE_SPEED_BUMP:{record_id}",
                    source_dataset="Kaggle_speed_bump_dataset",
                    image_reference=str(image_path),
                    annotation_reference=f"{audit_path}#line={line_number}",
                )
            )
    if not rows:
        raise ValueError("Kaggle speed-bump audit contains no retained candidates")
    return rows, hashes


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _mendeley_speed_bump_rows(images_root: Path, holdout_path: Path) -> tuple[list[dict[str, Any]], set[str]]:
    """Use only Mendeley speed-bump images that are not known cross-label conflicts."""
    if not images_root.is_dir() or not holdout_path.is_file():
        raise FileNotFoundError("Mendeley speed-bump folder and conflict holdout are both required")
    held_out_hashes: set[str] = set()
    with holdout_path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        for record in reader:
            if record.get("proposed_label") == "speed_bump":
                held_out_hashes.add(record["sha256"])
    image_paths = sorted(
        path
        for pattern in ("*.jpg", "*.jpeg", "*.png")
        for path in images_root.rglob(pattern)
        if path.is_file()
    )
    rows: list[dict[str, Any]] = []
    hashes: set[str] = set()
    for image_path in image_paths:
        source_hash = _sha256(image_path)
        if source_hash in held_out_hashes:
            continue
        if source_hash in hashes:
            raise ValueError(f"Mendeley selected speed-bump folder contains an exact duplicate: {image_path}")
        hashes.add(source_hash)
        rows.append(
            _speed_bump_partial_row(
                record_id=f"MENDELEY_SPEED_BREAKER:{image_path.name}",
                source_dataset="Mendeley_Manhole_SpeedBreaker",
                image_reference=str(image_path),
                annotation_reference=f"{images_root}#folder-label=Speed_Breaker",
            )
        )
    if not rows:
        raise ValueError("No conflict-safe Mendeley speed-bump records remain")
    return rows, hashes


def _existing_weak_class_rows(inventory_path: Path, project_root: Path) -> tuple[list[dict[str, Any]], set[str]]:
    """Reuse audited CeyMo and unpaved-road candidates as positive-only evidence.

    These sources verify their own named condition, but do not provide a full
    seven-condition truth table. All other conditions intentionally remain
    unknown in the generated rows.
    """
    if not inventory_path.is_file():
        raise FileNotFoundError(f"Missing V2 candidate inventory: {inventory_path}")
    selected: list[tuple[dict[str, str], str]] = []
    with inventory_path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        required = {
            "candidate_id",
            "source_id",
            "source_image_path",
            "source_annotation_path",
            "proposed_multiclass_label",
            "proposed_multilabels",
            "sha256",
        }
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError("V2 candidate inventory has an unexpected schema")
        for record in reader:
            if record["source_id"] == "CeyMo" and record["proposed_multilabels"] == "road_marking":
                selected.append((record, "road_marking"))
            elif (
                record["source_id"] in {"Road Quality Dataset (RQD)", "StreetSurfaceVis"}
                and record["proposed_multiclass_label"] == "unpaved_road"
            ):
                selected.append((record, "unpaved_road"))
    rows: list[dict[str, Any]] = []
    hashes: set[str] = set()
    for record, condition in selected:
        candidate_id = record["candidate_id"]
        source_hash = record["sha256"]
        image_relative_path = record["source_image_path"]
        annotation_relative_path = record["source_annotation_path"]
        if not candidate_id or not source_hash or not image_relative_path:
            raise ValueError("Selected weak-class candidate is incomplete")
        image_path = project_root / image_relative_path
        if not image_path.is_file():
            raise FileNotFoundError(f"Weak-class candidate image missing: {image_path}")
        if source_hash in hashes:
            raise ValueError(f"Selected weak-class candidates contain an exact duplicate: {candidate_id}")
        hashes.add(source_hash)
        annotation_reference = str(project_root / annotation_relative_path) if annotation_relative_path else ""
        rows.append(
            {
                "record_id": f"{record['source_id']}:{candidate_id}",
                "source_dataset": record["source_id"],
                "original_source_split": "source_candidate",
                "stable_group_id": f"{record['source_id']}:{candidate_id}",
                "image_reference": str(image_path),
                "annotation_reference": annotation_reference,
                **_coverage_fields({condition}, {condition}),
            }
        )
    if not rows:
        raise ValueError("No selected road-marking or unpaved-road candidates were found")
    return rows, hashes


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
    kaggle_speed_bump_audit: Path | None = None,
    project_root: Path | None = None,
    mendeley_speed_bump_root: Path | None = None,
    mendeley_conflict_holdout: Path | None = None,
    candidate_inventory: Path | None = None,
) -> dict[str, Any]:
    """Build and save the coverage manifest plus a compact verification summary."""
    rows = _svrdd_rows(svrdd_metadata, svrdd_images_root) + _rtk_rows(rtk_images_archive, rtk_annotations_archive)
    speed_bump_options = (kaggle_speed_bump_audit, mendeley_speed_bump_root, mendeley_conflict_holdout)
    if any(option is not None for option in speed_bump_options):
        if project_root is None or any(option is None for option in speed_bump_options):
            raise ValueError("All four speed-bump source arguments are required together")
        kaggle_rows, kaggle_hashes = _kaggle_speed_bump_rows(kaggle_speed_bump_audit, project_root)  # type: ignore[arg-type]
        mendeley_rows, mendeley_hashes = _mendeley_speed_bump_rows(mendeley_speed_bump_root, mendeley_conflict_holdout)  # type: ignore[arg-type]
        overlap = kaggle_hashes & mendeley_hashes
        if overlap:
            raise ValueError(f"Kaggle and Mendeley speed-bump sources overlap exactly: {len(overlap)} hashes")
        rows.extend(kaggle_rows)
        rows.extend(mendeley_rows)
    if candidate_inventory is not None:
        if project_root is None:
            raise ValueError("project_root is required when adding weak-class candidates")
        weak_class_rows, _ = _existing_weak_class_rows(candidate_inventory, project_root)
        rows.extend(weak_class_rows)
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
    parser.add_argument("--kaggle-speed-bump-audit", type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--mendeley-speed-bump-root", type=Path)
    parser.add_argument("--mendeley-conflict-holdout", type=Path)
    parser.add_argument("--candidate-inventory", type=Path, help="Existing audited CeyMo/RQD/StreetSurfaceVis inventory")
    args = parser.parse_args()
    result = build_manifest(
        svrdd_metadata=args.svrdd_metadata,
        svrdd_images_root=args.svrdd_images_root,
        rtk_images_archive=args.rtk_images_archive,
        rtk_annotations_archive=args.rtk_annotations_archive,
        output_csv=args.output_csv,
        summary_json=args.summary_json,
        kaggle_speed_bump_audit=args.kaggle_speed_bump_audit,
        project_root=args.project_root,
        mendeley_speed_bump_root=args.mendeley_speed_bump_root,
        mendeley_conflict_holdout=args.mendeley_conflict_holdout,
        candidate_inventory=args.candidate_inventory,
    )
    print(f"Built {result['total_records']} non-materialized coverage records: {args.output_csv}")
    for source_name, source_summary in result["sources"].items():
        print(f"- {source_name}: {source_summary['records']} records")


if __name__ == "__main__":
    main()
