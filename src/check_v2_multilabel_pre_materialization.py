"""Verify a planned multi-label split before creating any image folders.

This check joins the coverage manifest, image-readability audit, duplicate
reports, and non-materialized split plan.  It proves that every planned record
is readable, each safe group stays in one split, and every active label has
known and positive evidence in train, validation, and test.  It never copies,
moves, relabels, or trains on images.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

if __package__:
    from src.build_v2_multilabel_coverage_manifest import ACTIVE_CONDITIONS
else:
    from build_v2_multilabel_coverage_manifest import ACTIVE_CONDITIONS  # type: ignore[no-redef]


SPLITS = ("train", "validation", "test")
COVERAGE_FIELDS = ("planned_split", "condition", "records", "known_records", "positive_records")


def _read_rows(path: Path, required_fields: set[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        fields = set(reader.fieldnames or ())
        if not required_fields.issubset(fields):
            raise ValueError(f"{path.name} must contain: {sorted(required_fields)}")
        return list(reader)


def _index_unique(rows: list[dict[str, str]], key: str, report_name: str) -> dict[str, dict[str, str]]:
    indexed = {row[key]: row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError(f"{report_name} has duplicate {key} values")
    return indexed


def _binary(value: str, name: str, record_id: str) -> int:
    if value not in {"0", "1"}:
        raise ValueError(f"{record_id} has invalid {name}: {value!r}")
    return int(value)


def check_pre_materialization(
    manifest_rows: list[dict[str, str]],
    plan_rows: list[dict[str, str]],
    audit_rows: list[dict[str, str]],
    exact_rows: list[dict[str, str]],
    near_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Return coverage evidence or raise a clear error when the plan is unsafe."""
    manifest = _index_unique(manifest_rows, "record_id", "Manifest")
    plan = _index_unique(plan_rows, "record_id", "Split plan")
    audit = _index_unique(audit_rows, "record_id", "Image audit")
    if set(manifest) != set(plan) or set(manifest) != set(audit):
        raise ValueError("Manifest, split plan, and image audit must contain exactly the same record IDs")

    group_splits: dict[str, set[str]] = defaultdict(set)
    split_records: dict[str, list[str]] = {split: [] for split in SPLITS}
    for record_id, plan_row in plan.items():
        split = plan_row["planned_split"]
        if split not in SPLITS:
            raise ValueError(f"{record_id} has an invalid planned split: {split}")
        manifest_row, audit_row = manifest[record_id], audit[record_id]
        if plan_row["source_dataset"] != manifest_row["source_dataset"]:
            raise ValueError(f"{record_id} has different source names in manifest and split plan")
        if audit_row["readable"] != "yes":
            raise ValueError(f"{record_id} is not readable according to the image audit")
        if audit_row["image_reference"] != manifest_row["image_reference"]:
            raise ValueError(f"{record_id} has different image references in manifest and image audit")
        group_splits[plan_row["split_group_id"]].add(split)
        split_records[split].append(record_id)
    leaking_groups = [group_id for group_id, splits in group_splits.items() if len(splits) != 1]
    if leaking_groups:
        raise ValueError(f"Safe groups leaked across planned splits: {leaking_groups[:3]}")

    exact_splits: dict[str, set[str]] = defaultdict(set)
    for row in exact_rows:
        if row["record_id"] not in plan:
            raise ValueError(f"Exact-duplicate report references unknown record: {row['record_id']}")
        exact_splits[row["exact_duplicate_group_id"]].add(plan[row["record_id"]]["planned_split"])
    if any(len(splits) != 1 for splits in exact_splits.values()):
        raise ValueError("An exact-duplicate group leaks across planned splits")
    for row in near_rows:
        first, second = row["record_id_a"], row["record_id_b"]
        if first not in plan or second not in plan:
            raise ValueError(f"Near-duplicate report references unknown records: {first}, {second}")
        if plan[first]["planned_split"] != plan[second]["planned_split"]:
            raise ValueError(f"Likely near-duplicate pair leaks across planned splits: {first}, {second}")

    coverage: list[dict[str, str]] = []
    for split in SPLITS:
        if not split_records[split]:
            raise ValueError(f"Planned {split} split is empty")
        for condition in ACTIVE_CONDITIONS:
            known_count = 0
            positive_count = 0
            for record_id in split_records[split]:
                row = manifest[record_id]
                known = _binary(row[f"{condition}_known"], f"{condition}_known", record_id)
                present = row[f"{condition}_present"]
                if known == 0:
                    if present != "":
                        raise ValueError(f"{record_id} gives a value for unknown {condition}")
                    continue
                known_count += 1
                positive_count += _binary(present, f"{condition}_present", record_id)
            if known_count == 0 or positive_count == 0:
                raise ValueError(f"{split} has insufficient known positive coverage for {condition}")
            coverage.append(
                {
                    "planned_split": split,
                    "condition": condition,
                    "records": str(len(split_records[split])),
                    "known_records": str(known_count),
                    "positive_records": str(positive_count),
                }
            )
    summary = {
        "check": "v2_multilabel_pre_materialization",
        "status": "pass",
        "records": len(plan),
        "readable_records": len(audit),
        "safe_group_count": len(group_splits),
        "exact_duplicate_group_count": len(exact_splits),
        "likely_near_duplicate_pair_count": len(near_rows),
        "splits": {split: len(record_ids) for split, record_ids in split_records.items()},
        "decision": "The non-materialized plan is safe to materialize in a later approved step. No files were copied, moved, relabeled, or used for training by this check.",
    }
    return coverage, summary


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=COVERAGE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--split-plan", type=Path, required=True)
    parser.add_argument("--image-audit", type=Path, required=True)
    parser.add_argument("--exact-duplicates", type=Path, required=True)
    parser.add_argument("--near-duplicates", type=Path, required=True)
    parser.add_argument("--coverage-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    args = parser.parse_args()
    manifest_required = {"record_id", "source_dataset", "image_reference"} | {
        f"{condition}_{field}" for condition in ACTIVE_CONDITIONS for field in ("known", "present")
    }
    coverage, summary = check_pre_materialization(
        _read_rows(args.manifest, manifest_required),
        _read_rows(args.split_plan, {"record_id", "source_dataset", "split_group_id", "planned_split"}),
        _read_rows(args.image_audit, {"record_id", "image_reference", "readable"}),
        _read_rows(args.exact_duplicates, {"exact_duplicate_group_id", "record_id"}),
        _read_rows(args.near_duplicates, {"record_id_a", "record_id_b"}),
    )
    _write_csv(args.coverage_output, coverage)
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("Pre-materialization check: PASS")
    for split, count in summary["splits"].items():
        print(f"{split}: {count} records")


if __name__ == "__main__":
    main()
