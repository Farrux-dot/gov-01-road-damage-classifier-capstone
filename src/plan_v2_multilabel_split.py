"""Plan a safe 80/10/10 multi-label split without materializing images.

The planner assigns every previously audited split group to train, validation,
or test.  It keeps all records in a group together and tries to distribute
confirmed positive labels and known-label coverage across the three splits.
Unknown labels remain unknown; this script never turns them into negative
labels.  It writes a plan only and never copies, moves, or trains on images.
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


SPLIT_RATIOS = {"train": 0.80, "validation": 0.10, "test": 0.10}
PLAN_FIELDS = (
    "record_id",
    "source_dataset",
    "split_group_id",
    "group_size",
    "group_reason",
    "planned_split",
)


def _read_rows(path: Path, required_fields: set[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        fields = set(reader.fieldnames or ())
        if not required_fields.issubset(fields):
            raise ValueError(f"{path.name} must contain: {sorted(required_fields)}")
        return list(reader)


def _binary_value(value: str, field_name: str, record_id: str) -> int:
    if value not in {"0", "1"}:
        raise ValueError(f"{record_id} has invalid {field_name}: {value!r}")
    return int(value)


def _record_labels(row: dict[str, str]) -> tuple[dict[str, int], dict[str, int]]:
    """Read known and present fields without inventing labels for unknown data."""
    record_id = row["record_id"]
    known: dict[str, int] = {}
    present: dict[str, int] = {}
    for condition in ACTIVE_CONDITIONS:
        known_value = _binary_value(row[f"{condition}_known"], f"{condition}_known", record_id)
        present_value = row[f"{condition}_present"]
        if known_value == 0:
            if present_value != "":
                raise ValueError(f"{record_id} marks unknown {condition} as present or absent")
            known[condition] = 0
            present[condition] = 0
            continue
        present[condition] = _binary_value(present_value, f"{condition}_present", record_id)
        known[condition] = 1
    return known, present


def _empty_counts() -> dict[str, dict[str, int]]:
    return {
        "records": {"count": 0},
        "known": {condition: 0 for condition in ACTIVE_CONDITIONS},
        "present": {condition: 0 for condition in ACTIVE_CONDITIONS},
    }


def _group_rows(
    manifest_rows: list[dict[str, str]], group_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    manifest = {row["record_id"]: row for row in manifest_rows}
    grouped_ids = {row["record_id"] for row in group_rows}
    if len(manifest) != len(manifest_rows):
        raise ValueError("Manifest record_id values must be unique")
    if len(grouped_ids) != len(group_rows):
        raise ValueError("Split-group record_id values must be unique")
    if set(manifest) != grouped_ids:
        missing = sorted(set(manifest) - grouped_ids)
        extra = sorted(grouped_ids - set(manifest))
        raise ValueError(f"Manifest and split groups do not match (missing={missing[:3]}, extra={extra[:3]})")

    by_group: dict[str, list[dict[str, str]]] = defaultdict(list)
    for group_row in group_rows:
        record_id = group_row["record_id"]
        by_group[group_row["split_group_id"]].append(group_row)

    groups: list[dict[str, Any]] = []
    for group_id, members in by_group.items():
        expected_size = {member["group_size"] for member in members}
        expected_reason = {member["group_reason"] for member in members}
        if expected_size != {str(len(members))} or len(expected_reason) != 1:
            raise ValueError(f"Split group is internally inconsistent: {group_id}")
        counts = _empty_counts()
        for member in members:
            known, present = _record_labels(manifest[member["record_id"]])
            counts["records"]["count"] += 1
            for condition in ACTIVE_CONDITIONS:
                counts["known"][condition] += known[condition]
                counts["present"][condition] += present[condition]
        groups.append(
            {
                "split_group_id": group_id,
                "members": members,
                "counts": counts,
            }
        )
    return groups


def _score_assignment(
    group_counts: dict[str, dict[str, int]],
    current: dict[str, dict[str, dict[str, int]]],
    totals: dict[str, dict[str, int]],
    split: str,
) -> float:
    """Prefer the split with the greatest remaining label and record need."""
    ratio = SPLIT_RATIOS[split]
    score = 0.0
    for condition in ACTIVE_CONDITIONS:
        positive_total = totals["present"][condition]
        known_total = totals["known"][condition]
        if positive_total:
            need = max((positive_total * ratio) - current[split]["present"][condition], 0.0)
            score += group_counts["present"][condition] * need / positive_total
        if known_total:
            need = max((known_total * ratio) - current[split]["known"][condition], 0.0)
            score += 0.25 * group_counts["known"][condition] * need / known_total
    record_total = totals["records"]["count"]
    record_need = max((record_total * ratio) - current[split]["records"]["count"], 0.0)
    score += 0.50 * group_counts["records"]["count"] * record_need / record_total
    return score


def _add_counts(
    destination: dict[str, dict[str, int]], source: dict[str, dict[str, int]], multiplier: int
) -> None:
    for category in ("records", "known", "present"):
        for name, value in source[category].items():
            destination[category][name] += multiplier * value


def _imbalance_cost(current: dict[str, dict[str, dict[str, int]]], totals: dict[str, dict[str, int]]) -> float:
    """Measure departure from the requested ratios for records and evidence."""
    cost = 0.0
    weights = {"records": 0.50, "known": 0.25, "present": 1.00}
    for split, ratio in SPLIT_RATIOS.items():
        for category, weight in weights.items():
            for name, total in totals[category].items():
                if not total:
                    continue
                difference = (current[split][category][name] - (total * ratio)) / total
                cost += weight * difference * difference
    return cost


def _refine_assignments(
    groups: list[dict[str, Any]],
    assignments: dict[str, str],
    current: dict[str, dict[str, dict[str, int]]],
    totals: dict[str, dict[str, int]],
) -> None:
    """Move whole groups only when a move improves the overall balance."""
    for _ in range(6):
        changed = False
        for group in sorted(groups, key=lambda item: item["split_group_id"]):
            group_id = group["split_group_id"]
            original = assignments[group_id]
            baseline = _imbalance_cost(current, totals)
            best_split = original
            best_cost = baseline
            for candidate in SPLIT_RATIOS:
                if candidate == original:
                    continue
                _add_counts(current[original], group["counts"], -1)
                _add_counts(current[candidate], group["counts"], 1)
                candidate_cost = _imbalance_cost(current, totals)
                _add_counts(current[candidate], group["counts"], -1)
                _add_counts(current[original], group["counts"], 1)
                if candidate_cost < best_cost - 1e-12:
                    best_split = candidate
                    best_cost = candidate_cost
            if best_split != original:
                _add_counts(current[original], group["counts"], -1)
                _add_counts(current[best_split], group["counts"], 1)
                assignments[group_id] = best_split
                changed = True
        if not changed:
            return


def plan_split(
    manifest_rows: list[dict[str, str]], group_rows: list[dict[str, str]]
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Assign safe groups deterministically while balancing available evidence."""
    groups = _group_rows(manifest_rows, group_rows)
    totals = _empty_counts()
    for group in groups:
        for category in ("records", "known", "present"):
            for name, value in group["counts"][category].items():
                totals[category][name] += value
    current = {split: _empty_counts() for split in SPLIT_RATIOS}
    assignments: dict[str, str] = {}
    # Large and label-rich groups are placed first, when the planner has the
    # greatest freedom to keep the final proportions balanced.
    ordered_groups = sorted(
        groups,
        key=lambda group: (
            -sum(group["counts"]["present"].values()),
            -group["counts"]["records"]["count"],
            group["split_group_id"],
        ),
    )
    for group in ordered_groups:
        split = max(
            SPLIT_RATIOS,
            key=lambda candidate: (
                _score_assignment(group["counts"], current, totals, candidate),
                SPLIT_RATIOS[candidate],
            ),
        )
        assignments[group["split_group_id"]] = split
        for category in ("records", "known", "present"):
            for name, value in group["counts"][category].items():
                current[split][category][name] += value
    _refine_assignments(groups, assignments, current, totals)

    planned_rows: list[dict[str, str]] = []
    for group in groups:
        split = assignments[group["split_group_id"]]
        for member in group["members"]:
            planned_rows.append({**member, "planned_split": split})
    planned_rows.sort(key=lambda row: row["record_id"])
    summary = {
        "plan": "v2_multilabel_nonmaterialized_safe_split",
        "ratios": SPLIT_RATIOS,
        "records": len(planned_rows),
        "groups": len(groups),
        "actual": current,
        "decision": "This is an assignment plan only. No images were copied, moved, relabeled, materialized, or used for training. All records with one split_group_id stay in one planned_split.",
    }
    return planned_rows, summary


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=PLAN_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--split-groups", type=Path, required=True)
    parser.add_argument("--plan-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    args = parser.parse_args()
    required_manifest = {"record_id", "source_dataset"} | {
        f"{condition}_{field}" for condition in ACTIVE_CONDITIONS for field in ("known", "present")
    }
    manifest_rows = _read_rows(args.manifest, required_manifest)
    group_rows = _read_rows(args.split_groups, set(PLAN_FIELDS) - {"planned_split"})
    planned_rows, summary = plan_split(manifest_rows, group_rows)
    _write_csv(args.plan_output, planned_rows)
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Planned records: {summary['records']}")
    for split in SPLIT_RATIOS:
        print(f"{split}: {summary['actual'][split]['records']['count']} records")


if __name__ == "__main__":
    main()
