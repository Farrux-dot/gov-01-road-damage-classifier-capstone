"""Build a source-traceable, pre-split V2 candidate image inventory.

The tool inventories eligible records only. It does not copy images, alter raw
annotations, create train/validation/test splits, or train a model.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


SVRDD_CANDIDATE_SPLITS = ("train",)
SVRDD_RESERVED_SPLITS = ("validation", "test")
STREETSURFACEVIS_TO_V2 = {
    "Normal_asphalt": "normal_asphalt",
    "Unpaved_road": "unpaved_road",
}
CEYMO_ACCEPTED_STATUS = "pre_split_source_candidate"
MULTILABEL_KEYS = {
    "pothole_present": "pothole",
    "crack_present": "crack",
    "manhole_cover_present": "manhole_cover",
    "repaired_road_present": "repaired_road",
}
FIELDNAMES = (
    "candidate_id",
    "source_id",
    "source_url",
    "license_record",
    "original_source_split",
    "source_record_id",
    "source_image_path",
    "source_annotation_path",
    "review_sample_id",
    "task_eligibility",
    "boxes_available",
    "object_count",
    "object_labels",
    "object_label_counts",
    "proposed_multiclass_label",
    "proposed_multilabels",
    "review_basis",
    "candidate_status",
    "sha256",
    "exact_duplicate_group_id",
)


def file_digest(path: Path) -> str:
    """Return an exact SHA-256 content digest."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repository_relative(path: Path, repository_root: Path) -> str:
    """Return a safe repository-relative path or stop for an outside path."""
    try:
        return path.resolve().relative_to(repository_root.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(f"Path is outside the repository: {path}") from error


def checked_digest(path: Path) -> str:
    """Hash one required source image, stopping if it is missing."""
    if not path.is_file():
        raise FileNotFoundError(f"Candidate source image not found: {path}")
    return file_digest(path)


def labels_from_multilabels(values: dict[str, Any]) -> str:
    """Return stable semicolon-separated positive labels."""
    unsupported = set(values) - set(MULTILABEL_KEYS)
    if unsupported:
        raise ValueError(f"Unsupported SVRDD multi-label keys: {sorted(unsupported)}")
    return ";".join(
        MULTILABEL_KEYS[key]
        for key in MULTILABEL_KEYS
        if bool(values.get(key, False))
    )


def build_svrdd_candidates(
    repository_root: Path,
    annotations_dir: Path,
    extracted_dir: Path,
) -> list[dict[str, Any]]:
    """Create candidates from the SVRDD source training split only."""
    records: list[dict[str, Any]] = []
    for split in SVRDD_CANDIDATE_SPLITS:
        annotation_path = annotations_dir / f"{split}.v2.jsonl"
        if not annotation_path.is_file():
            raise FileNotFoundError(f"Missing converted SVRDD annotations: {annotation_path}")
        with annotation_path.open(encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                try:
                    item = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"Invalid JSON in {annotation_path} line {line_number}") from error
                image_id = str(item.get("image_id", "")).strip()
                file_name = str(item.get("file_name", "")).strip()
                if not image_id or not file_name:
                    raise ValueError(f"Missing SVRDD image_id or file_name in {annotation_path} line {line_number}")
                image_path = extracted_dir / split / Path(file_name)
                object_labels = [str(label) for label in item.get("objects", {}).get("v2_labels", [])]
                if not object_labels:
                    raise ValueError(f"SVRDD record has no mapped V2 objects: {split}/{image_id}")
                object_label_counts = Counter(object_labels)
                multiclass = str(item.get("multi_class_label", "")).strip()
                multilabels = labels_from_multilabels(item.get("multi_labels", {}))
                records.append(
                    {
                        "candidate_id": f"svrdd::{split}::{image_id}",
                        "source_id": "SVRDD_YOLO",
                        "source_url": "https://huggingface.co/datasets/ShuoZheLi/SVRDD_YOLO",
                        "license_record": "CC BY 4.0 stated on dataset card; recheck before redistribution",
                        "original_source_split": split,
                        "source_record_id": image_id,
                        "source_image_path": repository_relative(image_path, repository_root),
                        "source_annotation_path": repository_relative(annotation_path, repository_root),
                        "review_sample_id": "",
                        "task_eligibility": "multi_class;multi_label;object_detection",
                        "boxes_available": "yes",
                        "object_count": len(object_labels),
                        "object_labels": ";".join(sorted(set(object_labels))),
                        "object_label_counts": ";".join(
                            f"{label}:{count}" for label, count in sorted(object_label_counts.items())
                        ),
                        "proposed_multiclass_label": multiclass,
                        "proposed_multilabels": multilabels,
                        "review_basis": "source mapping accepted from 56-image training sanity sample",
                        "candidate_status": "pre_split_source_candidate",
                        "sha256": checked_digest(image_path),
                        "exact_duplicate_group_id": "",
                    }
                )
    return records


def build_v1_pothole_candidates(
    repository_root: Path,
    clean_split_dir: Path,
) -> list[dict[str, Any]]:
    """Create image-level candidates from V1 training potholes only."""
    pothole_dir = clean_split_dir / "train" / "Pothole"
    if not pothole_dir.is_dir():
        raise FileNotFoundError(f"Missing eligible V1 pothole folder: {pothole_dir}")
    records: list[dict[str, Any]] = []
    for image_path in sorted(path for path in pothole_dir.iterdir() if path.is_file()):
        records.append(
            {
                "candidate_id": f"v1::train::pothole::{image_path.name}",
                "source_id": "V1_Kaggle_pothole_detection",
                "source_url": "https://www.kaggle.com/datasets/abhinavkulshreshth/pothole-detection-dataset",
                "license_record": "CC0 listed by Kaggle at project planning; recheck before redistribution",
                "original_source_split": "train",
                "source_record_id": image_path.name,
                "source_image_path": repository_relative(image_path, repository_root),
                "source_annotation_path": "docs/clean_image_manifest.csv",
                "review_sample_id": "",
                "task_eligibility": "multi_class;multi_label",
                "boxes_available": "no",
                "object_count": "",
                "object_labels": "",
                "object_label_counts": "",
                "proposed_multiclass_label": "pothole",
                "proposed_multilabels": "pothole",
                "review_basis": "eligible V1 training split; validation and protected test reserved",
                "candidate_status": "pre_split_candidate_image_level_only_no_boxes",
                "sha256": checked_digest(image_path),
                "exact_duplicate_group_id": "",
            }
        )
    return records


def build_github_pothole_candidates(
    repository_root: Path,
    candidate_manifest: Path,
) -> list[dict[str, Any]]:
    """Create box-labelled pothole candidates from the approved GitHub audit manifest."""
    if not candidate_manifest.is_file():
        raise FileNotFoundError(f"Missing GitHub pothole candidate manifest: {candidate_manifest}")
    records: list[dict[str, Any]] = []
    with candidate_manifest.open(newline="", encoding="utf-8-sig") as file:
        for row_number, row in enumerate(csv.DictReader(file), start=2):
            decision = str(row.get("decision", "")).strip().lower()
            if decision == "exclude":
                continue
            if decision != "keep":
                raise ValueError(f"Unsupported GitHub pothole decision on row {row_number}: {decision}")
            source_record_id = str(row.get("source_id", "")).strip()
            source_path = str(row.get("relative_image_path", "")).strip().replace("\\", "/")
            annotation_path = str(row.get("relative_label_path", "")).strip().replace("\\", "/")
            expected_sha256 = str(row.get("sha256", "")).strip().lower()
            valid_boxes = int(str(row.get("valid_pothole_boxes", "0")).strip())
            if not source_record_id or not source_path or not annotation_path or not expected_sha256:
                raise ValueError(f"Incomplete GitHub pothole record on row {row_number}")
            if valid_boxes <= 0:
                raise ValueError(f"GitHub pothole candidate has no valid boxes on row {row_number}")
            image_path = repository_root / Path(source_path)
            label_path = repository_root / Path(annotation_path)
            actual_sha256 = checked_digest(image_path)
            if actual_sha256 != expected_sha256:
                raise ValueError(f"GitHub pothole SHA-256 mismatch on row {row_number}: {source_path}")
            if not label_path.is_file():
                raise FileNotFoundError(f"Missing GitHub pothole YOLO label: {label_path}")
            records.append(
                {
                    "candidate_id": f"github_pothole::{source_record_id}",
                    "source_id": "jaygala24_pothole_detection",
                    "source_url": "https://github.com/jaygala24/pothole-detection",
                    "license_record": "MIT licence in the source repository; recheck before redistribution",
                    "original_source_split": "unsplit_source_collection",
                    "source_record_id": source_record_id,
                    "source_image_path": repository_relative(image_path, repository_root),
                    "source_annotation_path": repository_relative(label_path, repository_root),
                    "review_sample_id": "",
                    "task_eligibility": "multi_class;multi_label;object_detection",
                    "boxes_available": "yes",
                    "object_count": valid_boxes,
                    "object_labels": "pothole",
                    "object_label_counts": f"pothole:{valid_boxes}",
                    "proposed_multiclass_label": "pothole",
                    "proposed_multilabels": "pothole",
                    "review_basis": "source YOLO boxes; duplicate and invalid-box exclusions recorded in audit; human visual quality approved",
                    "candidate_status": "pre_split_source_candidate",
                    "sha256": actual_sha256,
                    "exact_duplicate_group_id": "",
                }
            )
    return records


def build_streetsurfacevis_candidates(
    repository_root: Path,
    candidate_manifest: Path,
) -> list[dict[str, Any]]:
    """Create multi-class candidates from eligible StreetSurfaceVis training records."""
    if not candidate_manifest.is_file():
        raise FileNotFoundError(f"Missing StreetSurfaceVis candidate manifest: {candidate_manifest}")
    records: list[dict[str, Any]] = []
    with candidate_manifest.open(newline="", encoding="utf-8-sig") as file:
        for row_number, row in enumerate(csv.DictReader(file), start=2):
            if str(row.get("official_train", "")).strip().lower() != "true":
                continue
            if str(row.get("resolution_decision", "")).strip().lower() != "eligible":
                continue
            review_decision = str(row.get("human_review_decision", "")).strip()
            if review_decision.lower() in {"exclude", "unclear"}:
                continue
            if review_decision and review_decision.lower() != "keep":
                raise ValueError(
                    f"Unsupported StreetSurfaceVis review decision on row {row_number}: {review_decision}"
                )
            source_label = str(row.get("candidate_label", "")).strip()
            if source_label not in STREETSURFACEVIS_TO_V2:
                raise ValueError(
                    f"Unsupported StreetSurfaceVis candidate label on row {row_number}: {source_label}"
                )
            image_id = str(row.get("image_id", "")).strip()
            source_path = str(row.get("relative_image_path", "")).strip().replace("\\", "/")
            expected_sha256 = str(row.get("sha256", "")).strip().lower()
            if not image_id or not source_path or not expected_sha256:
                raise ValueError(f"Incomplete StreetSurfaceVis record on row {row_number}")
            image_path = repository_root / Path(source_path)
            actual_sha256 = checked_digest(image_path)
            if actual_sha256 != expected_sha256:
                raise ValueError(f"StreetSurfaceVis SHA-256 mismatch on row {row_number}: {source_path}")
            proposed_label = STREETSURFACEVIS_TO_V2[source_label]
            sample_id = str(row.get("review_sample_id", "")).strip()
            records.append(
                {
                    "candidate_id": f"streetsurfacevis::train::{image_id}",
                    "source_id": "StreetSurfaceVis",
                    "source_url": "https://zenodo.org/records/11449977",
                    "license_record": "CC-BY-SA stated on Zenodo record; recheck before redistribution",
                    "original_source_split": "train",
                    "source_record_id": image_id,
                    "source_image_path": repository_relative(image_path, repository_root),
                    "source_annotation_path": repository_relative(candidate_manifest, repository_root),
                    "review_sample_id": sample_id,
                    "task_eligibility": "multi_class",
                    "boxes_available": "no",
                    "object_count": "",
                    "object_labels": "",
                    "object_label_counts": "",
                    "proposed_multiclass_label": proposed_label,
                    "proposed_multilabels": "",
                    "review_basis": (
                        "individual human approval in StreetSurfaceVis sample review"
                        if review_decision.lower() == "keep"
                        else "source label supported by deterministic human-reviewed sample"
                    ),
                    "candidate_status": (
                        "pre_split_individually_reviewed_candidate"
                        if review_decision.lower() == "keep"
                        else "pre_split_source_labeled_sample_supported_candidate"
                    ),
                    "sha256": actual_sha256,
                    "exact_duplicate_group_id": "",
                }
            )
    return records


def build_ceymo_candidates(
    repository_root: Path,
    candidate_manifest: Path,
) -> list[dict[str, Any]]:
    """Create road-marking candidates from the duplicate-safe CeyMo manifest."""
    if not candidate_manifest.is_file():
        raise FileNotFoundError(f"Missing CeyMo candidate manifest: {candidate_manifest}")
    records: list[dict[str, Any]] = []
    with candidate_manifest.open(newline="", encoding="utf-8-sig") as file:
        for row_number, row in enumerate(csv.DictReader(file), start=2):
            status = str(row.get("candidate_status", "")).strip()
            if status == "exclude_exact_duplicate":
                continue
            if status != CEYMO_ACCEPTED_STATUS:
                raise ValueError(f"Unsupported CeyMo candidate status on row {row_number}: {status}")
            source_record_id = str(row.get("source_record_id", "")).strip()
            source_path = str(row.get("source_image_path", "")).strip().replace("\\", "/")
            annotation_path = str(row.get("source_annotation_path", "")).strip().replace("\\", "/")
            expected_sha256 = str(row.get("sha256", "")).strip().lower()
            source_subtype_counts = str(row.get("source_subtype_counts", "")).strip()
            mapped_object_count = int(str(row.get("mapped_object_count", "0")).strip())
            if not source_record_id or not source_path or not annotation_path or not expected_sha256:
                raise ValueError(f"Incomplete CeyMo candidate record on row {row_number}")
            if mapped_object_count <= 0:
                raise ValueError(f"CeyMo candidate has no mapped objects on row {row_number}")
            image_path = repository_root / Path(source_path)
            xml_path = repository_root / Path(annotation_path)
            actual_sha256 = checked_digest(image_path)
            if actual_sha256 != expected_sha256:
                raise ValueError(f"CeyMo SHA-256 mismatch on row {row_number}: {source_path}")
            if not xml_path.is_file():
                raise FileNotFoundError(f"Missing CeyMo XML annotation: {xml_path}")
            records.append(
                {
                    "candidate_id": f"ceymo::train::{source_record_id}",
                    "source_id": "CeyMo",
                    "source_url": "https://github.com/oshadajay/CeyMo",
                    "license_record": (
                        "MIT repository licence; confirm dataset-file redistribution coverage"
                    ),
                    "original_source_split": "train",
                    "source_record_id": source_record_id,
                    "source_image_path": repository_relative(image_path, repository_root),
                    "source_annotation_path": repository_relative(xml_path, repository_root),
                    "review_sample_id": "",
                    "task_eligibility": "multi_label;object_detection",
                    "boxes_available": "yes",
                    "object_count": mapped_object_count,
                    "object_labels": "road_marking",
                    "object_label_counts": f"road_marking:{mapped_object_count}",
                    "proposed_multiclass_label": "",
                    "proposed_multilabels": "road_marking",
                    "review_basis": (
                        "audited source labels plus student-approved visual quality; "
                        f"source subtypes={source_subtype_counts}"
                    ),
                    "candidate_status": "pre_split_source_candidate",
                    "sha256": actual_sha256,
                    "exact_duplicate_group_id": str(row.get("exact_duplicate_group_id", "")).strip(),
                }
            )
    return records


def build_hf_manhole_candidates(
    repository_root: Path,
    audit_manifest: Path,
) -> list[dict[str, Any]]:
    """Create image-level manhole-cover candidates from the audited source train split."""
    if not audit_manifest.is_file():
        raise FileNotFoundError(f"Missing Hugging Face manhole audit manifest: {audit_manifest}")
    records: list[dict[str, Any]] = []
    with audit_manifest.open(newline="", encoding="utf-8-sig") as file:
        for row_number, row in enumerate(csv.DictReader(file), start=2):
            if str(row.get("candidate_status", "")).strip() != "source_train_manhole_candidate":
                continue
            source_record_id = str(row.get("source_record_id", "")).strip()
            source_path = str(row.get("relative_image_path", "")).strip().replace("\\\\", "/")
            expected_sha256 = str(row.get("sha256", "")).strip().lower()
            if not source_record_id or not source_path or not expected_sha256:
                raise ValueError(f"Incomplete Hugging Face manhole record on row {row_number}")
            image_path = repository_root / Path(source_path)
            actual_sha256 = checked_digest(image_path)
            if actual_sha256 != expected_sha256:
                raise ValueError(f"Hugging Face manhole SHA-256 mismatch on row {row_number}: {source_path}")
            records.append(
                {
                    "candidate_id": f"hf_manhole::{source_record_id}",
                    "source_id": "delima87_manhole_covers_dataset",
                    "source_url": "https://huggingface.co/datasets/delima87/manhole_covers_dataset",
                    "license_record": "Apache-2.0 stated on dataset card; recheck before redistribution",
                    "original_source_split": "train",
                    "source_record_id": source_record_id,
                    "source_image_path": repository_relative(image_path, repository_root),
                    "source_annotation_path": repository_relative(audit_manifest, repository_root),
                    "review_sample_id": "",
                    "task_eligibility": "multi_class;multi_label",
                    "boxes_available": "no",
                    "object_count": "",
                    "object_labels": "",
                    "object_label_counts": "",
                    "proposed_multiclass_label": "manhole_cover",
                    "proposed_multilabels": "manhole_cover",
                    "review_basis": "audited source train folder label manhole; image-level candidate only, no boxes",
                    "candidate_status": "pre_split_source_labeled_candidate_image_level_only_no_boxes",
                    "sha256": actual_sha256,
                    "exact_duplicate_group_id": str(row.get("exact_duplicate_group_id", "")).strip(),
                }
            )
    return records


def mark_exact_duplicates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mark exact duplicate groups without silently deleting any candidate."""
    by_hash: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_hash[str(record["sha256"])].append(record)
    duplicate_groups = [group for group in by_hash.values() if len(group) > 1]
    for index, group in enumerate(sorted(duplicate_groups, key=lambda items: str(items[0]["sha256"])), start=1):
        group_id = f"exact_dup_{index:04d}"
        for record in group:
            record["exact_duplicate_group_id"] = group_id
            record["candidate_status"] = "hold_exact_duplicate_before_split"
    return records


def validate_inventory(records: Iterable[dict[str, Any]]) -> None:
    """Stop on missing, duplicate, or unsafe inventory identifiers and paths."""
    records = list(records)
    candidate_ids = [str(record["candidate_id"]) for record in records]
    source_paths = [str(record["source_image_path"]) for record in records]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("Candidate IDs are not unique")
    if any(Path(path).is_absolute() or ":\\" in path for path in source_paths):
        raise ValueError("Inventory contains an absolute source path")
    if any(path.startswith("data/processed/clean_split/validation/") for path in source_paths):
        raise ValueError("V1 validation image entered the candidate inventory")
    if any(path.startswith("data/processed/clean_split/test/") for path in source_paths):
        raise ValueError("V1 protected-test image entered the candidate inventory")
    for reserved_split in SVRDD_RESERVED_SPLITS:
        prefix = f"data/raw/v2/svrdd/extracted/{reserved_split}/"
        if any(path.startswith(prefix) for path in source_paths):
            raise ValueError(f"SVRDD reserved {reserved_split} image entered the candidate inventory")


def write_inventory(records: list[dict[str, Any]], output_path: Path) -> None:
    """Write the stable candidate inventory CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Return non-model inventory evidence for documentation."""
    source_counts = Counter(str(record["source_id"]) for record in records)
    multiclass_counts = Counter(str(record["proposed_multiclass_label"]) for record in records)
    task_counts = Counter(str(record["task_eligibility"]) for record in records)
    box_counts = Counter(str(record.get("boxes_available", "")) for record in records)
    multilabel_positive_counts: Counter[str] = Counter()
    object_counts: Counter[str] = Counter()
    for record in records:
        for label in filter(None, str(record.get("proposed_multilabels", "")).split(";")):
            multilabel_positive_counts[label] += 1
        for item in filter(None, str(record.get("object_label_counts", "")).split(";")):
            label, count = item.rsplit(":", maxsplit=1)
            object_counts[label] += int(count)
    duplicate_group_counts = Counter(
        str(record["exact_duplicate_group_id"])
        for record in records
        if record["exact_duplicate_group_id"]
    )
    duplicate_groups = {
        group_id for group_id, count in duplicate_group_counts.items() if count > 1
    }
    duplicate_records = sum(duplicate_group_counts[group_id] for group_id in duplicate_groups)
    return {
        "candidate_image_records": len(records),
        "counts_by_source": dict(sorted(source_counts.items())),
        "counts_by_proposed_multiclass_label": dict(sorted(multiclass_counts.items())),
        "counts_by_positive_multilabel": dict(sorted(multilabel_positive_counts.items())),
        "object_counts_by_label": dict(sorted(object_counts.items())),
        "counts_by_task_eligibility": dict(sorted(task_counts.items())),
        "counts_by_boxes_available": dict(sorted(box_counts.items())),
        "exact_duplicate_group_count": len(duplicate_groups),
        "records_in_exact_duplicate_groups": duplicate_records,
        "v1_validation_or_test_records": sum(
            str(record["source_image_path"]).startswith(
                ("data/processed/clean_split/validation/", "data/processed/clean_split/test/")
            )
            for record in records
        ),
        "svrdd_candidate_source_splits": list(SVRDD_CANDIDATE_SPLITS),
        "svrdd_reserved_source_splits": list(SVRDD_RESERVED_SPLITS),
        "inventory_status": "pre_split_candidates_only_not_ready_for_training",
    }


def build_inventory(
    repository_root: Path,
    svrdd_annotations_dir: Path,
    svrdd_extracted_dir: Path,
    v1_clean_split_dir: Path,
    github_pothole_candidate_manifest: Path,
    streetsurfacevis_candidate_manifest: Path,
    ceymo_candidate_manifest: Path,
    hf_manhole_audit_manifest: Path,
) -> list[dict[str, Any]]:
    """Build and validate all currently eligible candidate sources."""
    records = [
        *build_svrdd_candidates(repository_root, svrdd_annotations_dir, svrdd_extracted_dir),
        *build_v1_pothole_candidates(repository_root, v1_clean_split_dir),
        *build_github_pothole_candidates(repository_root, github_pothole_candidate_manifest),
        *build_streetsurfacevis_candidates(repository_root, streetsurfacevis_candidate_manifest),
        *build_ceymo_candidates(repository_root, ceymo_candidate_manifest),
        *build_hf_manhole_candidates(repository_root, hf_manhole_audit_manifest),
    ]
    records = sorted(records, key=lambda record: str(record["candidate_id"]))
    mark_exact_duplicates(records)
    validate_inventory(records)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--svrdd-annotations-dir", type=Path, required=True)
    parser.add_argument("--svrdd-extracted-dir", type=Path, required=True)
    parser.add_argument("--v1-clean-split-dir", type=Path, required=True)
    parser.add_argument("--github-pothole-candidate-manifest", type=Path, required=True)
    parser.add_argument("--streetsurfacevis-candidate-manifest", type=Path, required=True)
    parser.add_argument("--ceymo-candidate-manifest", type=Path, required=True)
    parser.add_argument("--hf-manhole-audit-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    records = build_inventory(
        args.repo_root,
        args.svrdd_annotations_dir,
        args.svrdd_extracted_dir,
        args.v1_clean_split_dir,
        args.github_pothole_candidate_manifest,
        args.streetsurfacevis_candidate_manifest,
        args.ceymo_candidate_manifest,
        args.hf_manhole_audit_manifest,
    )
    report = summarize(records)
    write_inventory(records, args.output)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Saved candidate inventory: {args.output}")
    print(f"Saved inventory report: {args.report}")


if __name__ == "__main__":
    main()
