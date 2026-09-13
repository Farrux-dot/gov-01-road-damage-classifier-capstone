"""Build a duplicate-safe, source-traceable CeyMo candidate manifest.

The tool reads the audited CeyMo training images and Pascal VOC XML files.
It does not alter raw files, create a train/validation/test split, or train a
model. Exact duplicate images are recorded, and only one deterministic copy
from each duplicate group is accepted as a pre-split candidate.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from src.ceymo_v2_mapping import map_ceymo_label


FIELDNAMES = (
    "source_record_id",
    "source_image_path",
    "source_annotation_path",
    "source_subtype_labels",
    "source_subtype_counts",
    "mapped_object_count",
    "mapped_object_label_counts",
    "road_marking_present",
    "sha256",
    "exact_duplicate_group_id",
    "duplicate_role",
    "selection_rule",
    "candidate_status",
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


def read_xml_labels(path: Path) -> list[str]:
    """Read and validate source labels from one audited CeyMo XML file."""
    try:
        annotation = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as error:
        raise ValueError(f"Invalid CeyMo XML annotation: {path}") from error
    labels = [(item.findtext("name") or "").strip() for item in annotation.findall("object")]
    if not labels:
        raise ValueError(f"CeyMo annotation has no road-marking objects: {path}")
    for label in labels:
        map_ceymo_label(label)
    return labels


def choose_duplicate_keeper(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep the copy with most objects, then the alphabetically first stem."""
    return sorted(
        records,
        key=lambda record: (-int(record["mapped_object_count"]), str(record["source_record_id"])),
    )[0]


def build_manifest_records(
    repository_root: Path,
    images_dir: Path,
    annotations_dir: Path,
) -> list[dict[str, Any]]:
    """Build all candidate and duplicate-exclusion records."""
    if not images_dir.is_dir():
        raise FileNotFoundError(f"Missing CeyMo images folder: {images_dir}")
    if not annotations_dir.is_dir():
        raise FileNotFoundError(f"Missing CeyMo XML folder: {annotations_dir}")

    records: list[dict[str, Any]] = []
    for image_path in sorted(images_dir.glob("*.jpg"), key=lambda path: path.stem):
        annotation_path = annotations_dir / f"{image_path.stem}.xml"
        if not annotation_path.is_file():
            raise FileNotFoundError(f"Missing CeyMo XML annotation: {annotation_path}")
        labels = read_xml_labels(annotation_path)
        subtype_counts = Counter(labels)
        records.append(
            {
                "source_record_id": image_path.stem,
                "source_image_path": repository_relative(image_path, repository_root),
                "source_annotation_path": repository_relative(annotation_path, repository_root),
                "source_subtype_labels": ";".join(sorted(subtype_counts)),
                "source_subtype_counts": ";".join(
                    f"{label}:{count}" for label, count in sorted(subtype_counts.items())
                ),
                "mapped_object_count": len(labels),
                "mapped_object_label_counts": f"road_marking:{len(labels)}",
                "road_marking_present": "yes",
                "sha256": file_digest(image_path),
                "exact_duplicate_group_id": "",
                "duplicate_role": "unique",
                "selection_rule": "audited_source_training_record",
                "candidate_status": "pre_split_source_candidate",
            }
        )

    by_hash: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_hash[str(record["sha256"])].append(record)
    duplicate_groups = [group for group in by_hash.values() if len(group) > 1]
    for index, group in enumerate(
        sorted(duplicate_groups, key=lambda items: str(items[0]["sha256"])), start=1
    ):
        group_id = f"ceymo_exact_dup_{index:04d}"
        keeper = choose_duplicate_keeper(group)
        for record in group:
            record["exact_duplicate_group_id"] = group_id
            if record is keeper:
                record["duplicate_role"] = "keeper"
                record["selection_rule"] = "duplicate_keeper_most_objects_then_source_id"
            else:
                record["duplicate_role"] = "redundant_copy"
                record["selection_rule"] = "excluded_exact_duplicate"
                record["candidate_status"] = "exclude_exact_duplicate"

    return sorted(records, key=lambda record: str(record["source_record_id"]))


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Return transparent, non-model manifest counts."""
    accepted = [record for record in records if record["candidate_status"] == "pre_split_source_candidate"]
    excluded = [record for record in records if record["candidate_status"] == "exclude_exact_duplicate"]
    return {
        "source_image_records": len(records),
        "accepted_candidate_images": len(accepted),
        "excluded_exact_duplicate_images": len(excluded),
        "accepted_road_marking_objects": sum(int(record["mapped_object_count"]) for record in accepted),
        "exact_duplicate_group_count": len(
            {record["exact_duplicate_group_id"] for record in records if record["exact_duplicate_group_id"]}
        ),
        "manifest_status": "pre_split_candidates_only_not_ready_for_training",
    }


def write_manifest(records: list[dict[str, Any]], output_path: Path) -> None:
    """Write the stable CeyMo manifest CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--images-dir", type=Path, required=True)
    parser.add_argument("--annotations-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    records = build_manifest_records(args.repo_root, args.images_dir, args.annotations_dir)
    write_manifest(records, args.output)
    print(summarize(records))
    print(f"Saved CeyMo candidate manifest: {args.output}")


if __name__ == "__main__":
    main()
