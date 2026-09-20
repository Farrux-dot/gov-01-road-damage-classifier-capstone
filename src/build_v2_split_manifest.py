"""Build a deterministic, source-aware V2 multi-class split manifest.

The script reads the pre-split candidate inventory and writes a CSV *plan*.
It never copies images, changes raw data, or starts model training.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


SPLIT_NAMES = ("train", "validation", "protected_test")
MANIFEST_FIELDS = (
    "candidate_id",
    "source_id",
    "original_source_split",
    "source_record_id",
    "source_image_path",
    "sha256",
    "proposed_multiclass_label",
    "split_group_id",
    "split",
    "manifest_status",
)


def is_multiclass_candidate(row: dict[str, str]) -> bool:
    """Return true only for records with one declared multi-class label."""
    return bool(row["proposed_multiclass_label"].strip()) and "multi_class" in row[
        "task_eligibility"
    ].split(";")


def group_id(row: dict[str, str]) -> str:
    """Keep any future records from the same source image in one split."""
    return f"{row['source_id'].strip()}::{row['source_record_id'].strip()}"


def stable_order(seed: int, value: str) -> str:
    """Create a stable pseudo-random order without depending on machine state."""
    return hashlib.sha256(f"{seed}:{value}".encode("utf-8")).hexdigest()


def split_counts(group_count: int) -> dict[str, int]:
    """Return 70/15/15 counts while keeping every small stratum in training."""
    if group_count < 3:
        return {"train": group_count, "validation": 0, "protected_test": 0}
    validation = max(1, round(group_count * 0.15))
    protected_test = max(1, round(group_count * 0.15))
    train = group_count - validation - protected_test
    if train < 1:
        return {"train": group_count, "validation": 0, "protected_test": 0}
    return {"train": train, "validation": validation, "protected_test": protected_test}


def build_manifest(rows: Iterable[dict[str, str]], seed: int) -> list[dict[str, str]]:
    """Assign complete source-image groups within each label/source stratum."""
    eligible = [row for row in rows if is_multiclass_candidate(row)]
    groups: dict[tuple[str, str], dict[str, list[dict[str, str]]]] = defaultdict(dict)

    for row in eligible:
        label = row["proposed_multiclass_label"].strip()
        source = row["source_id"].strip()
        image_group = group_id(row)
        key = (label, source)
        existing = groups[key].setdefault(image_group, [])
        if existing and any(
            previous["proposed_multiclass_label"].strip() != label for previous in existing
        ):
            raise ValueError(f"Conflicting primary labels inside split group: {image_group}")
        existing.append(row)

    assignments: dict[str, str] = {}
    for (label, source), grouped_rows in sorted(groups.items()):
        ordered_groups = sorted(
            grouped_rows,
            key=lambda value: stable_order(seed, f"{label}:{source}:{value}"),
        )
        counts = split_counts(len(ordered_groups))
        train_end = counts["train"]
        validation_end = train_end + counts["validation"]
        for index, image_group in enumerate(ordered_groups):
            if index < train_end:
                assignments[image_group] = "train"
            elif index < validation_end:
                assignments[image_group] = "validation"
            else:
                assignments[image_group] = "protected_test"

    manifest: list[dict[str, str]] = []
    for row in sorted(eligible, key=lambda item: item["candidate_id"]):
        image_group = group_id(row)
        manifest.append(
            {
                "candidate_id": row["candidate_id"].strip(),
                "source_id": row["source_id"].strip(),
                "original_source_split": row["original_source_split"].strip(),
                "source_record_id": row["source_record_id"].strip(),
                "source_image_path": row["source_image_path"].strip(),
                "sha256": row["sha256"].strip(),
                "proposed_multiclass_label": row["proposed_multiclass_label"].strip(),
                "split_group_id": image_group,
                "split": assignments[image_group],
                "manifest_status": "proposed_not_materialized",
            }
        )
    return manifest


def validate_manifest(manifest: list[dict[str, str]]) -> None:
    """Stop if one candidate/group is missing or crosses split boundaries."""
    candidate_ids = [row["candidate_id"] for row in manifest]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("A candidate ID appears more than once in the split manifest")
    group_splits: dict[str, set[str]] = defaultdict(set)
    for row in manifest:
        if row["split"] not in SPLIT_NAMES:
            raise ValueError(f"Unsupported split: {row['split']}")
        group_splits[row["split_group_id"]].add(row["split"])
    leaked_groups = [group for group, values in group_splits.items() if len(values) > 1]
    if leaked_groups:
        raise ValueError(f"Split-group leakage found: {leaked_groups[:5]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    with args.inventory.open(newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))
    required = {
        "candidate_id",
        "source_id",
        "source_record_id",
        "source_image_path",
        "sha256",
        "task_eligibility",
        "proposed_multiclass_label",
    }
    missing_columns = required - set(rows[0] if rows else ())
    if missing_columns:
        raise ValueError(f"Inventory is missing columns: {sorted(missing_columns)}")

    manifest = build_manifest(rows, args.seed)
    validate_manifest(manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(manifest)

    report = {
        "seed": args.seed,
        "manifest_status": "proposed_not_materialized",
        "candidate_records": len(manifest),
        "split_counts": dict(sorted(Counter(row["split"] for row in manifest).items())),
        "label_split_counts": {
            label: dict(sorted(Counter(row["split"] for row in manifest if row["proposed_multiclass_label"] == label).items()))
            for label in sorted({row["proposed_multiclass_label"] for row in manifest})
        },
        "source_split_counts": {
            source: dict(sorted(Counter(row["split"] for row in manifest if row["source_id"] == source).items()))
            for source in sorted({row["source_id"] for row in manifest})
        },
        "split_group_count": len({row["split_group_id"] for row in manifest}),
        "decision": "Manifest passed structural checks; near-duplicate review and explicit approval are still required before materializing files or training.",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"Manifest records: {len(manifest)}")
    print(f"Split counts: {report['split_counts']}")
    print(f"Split groups: {report['split_group_count']}")
    print(f"Manifest written: {args.output}")
    print(f"Report written: {args.report}")


if __name__ == "__main__":
    main()
