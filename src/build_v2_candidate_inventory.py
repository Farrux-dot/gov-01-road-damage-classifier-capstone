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
PAVEBENCH_TO_V2 = {
    "alligator": "crack",
    "crack": "crack",
    "patch": "repaired_road",
}
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


def build_pavebench_candidates(
    repository_root: Path,
    review_manifest: Path,
) -> list[dict[str, Any]]:
    """Create candidates only from individually approved PaveBench records."""
    if not review_manifest.is_file():
        raise FileNotFoundError(f"Missing PaveBench review manifest: {review_manifest}")
    records: list[dict[str, Any]] = []
    with review_manifest.open(newline="", encoding="utf-8-sig") as file:
        for row_number, row in enumerate(csv.DictReader(file), start=2):
            if row.get("record_action") != "candidate_keep_reviewed_sample":
                continue
            source_class = str(row.get("source_class", "")).strip().lower()
            if source_class not in PAVEBENCH_TO_V2:
                raise ValueError(f"Unsupported approved PaveBench class on row {row_number}: {source_class}")
            proposed_label = PAVEBENCH_TO_V2[source_class]
            sample_id = str(row.get("sample_id", "")).strip()
            source_path = str(row.get("source_file", "")).strip().replace("\\", "/")
            image_path = repository_root / Path(source_path)
            records.append(
                {
                    "candidate_id": f"pavebench::{sample_id}",
                    "source_id": "PaveBench_detection_reviewed",
                    "source_url": "https://huggingface.co/datasets/VVQNN/PaveBench",
                    "license_record": "CC BY-NC-SA 4.0 stated on dataset card",
                    "original_source_split": "train",
                    "source_record_id": image_path.name,
                    "source_image_path": repository_relative(image_path, repository_root),
                    "source_annotation_path": "data/raw/v2/pavebench/data/Distress_Detection/annotations/instances_train.json",
                    "review_sample_id": sample_id,
                    "task_eligibility": "multi_class;multi_label;object_detection",
                    "boxes_available": "yes",
                    "object_count": 1,
                    "object_labels": proposed_label,
                    "object_label_counts": f"{proposed_label}:1",
                    "proposed_multiclass_label": proposed_label,
                    "proposed_multilabels": proposed_label,
                    "review_basis": "individual human approval in detection-label review",
                    "candidate_status": "pre_split_individually_reviewed_candidate",
                    "sha256": checked_digest(image_path),
                    "exact_duplicate_group_id": "",
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
    duplicate_groups = {
        str(record["exact_duplicate_group_id"])
        for record in records
        if record["exact_duplicate_group_id"]
    }
    duplicate_records = sum(bool(record["exact_duplicate_group_id"]) for record in records)
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
    pavebench_review_manifest: Path,
) -> list[dict[str, Any]]:
    """Build and validate all currently eligible candidate sources."""
    records = [
        *build_svrdd_candidates(repository_root, svrdd_annotations_dir, svrdd_extracted_dir),
        *build_v1_pothole_candidates(repository_root, v1_clean_split_dir),
        *build_pavebench_candidates(repository_root, pavebench_review_manifest),
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
    parser.add_argument("--pavebench-review-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    records = build_inventory(
        args.repo_root,
        args.svrdd_annotations_dir,
        args.svrdd_extracted_dir,
        args.v1_clean_split_dir,
        args.pavebench_review_manifest,
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
