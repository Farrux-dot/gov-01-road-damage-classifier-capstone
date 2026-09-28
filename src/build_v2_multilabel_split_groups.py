"""Create safe, non-materialized split groups from the multi-label audit.

Images linked by an exact duplicate or a likely near-duplicate relationship
receive the same split-group ID.  A later split step must assign an entire
group to train, validation, or test together.  This script only writes a
planning table; it never copies, deletes, relabels, or splits images.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path


GROUP_FIELDS = (
    "record_id",
    "source_dataset",
    "split_group_id",
    "group_size",
    "group_reason",
)


def _read_rows(path: Path, required_fields: set[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        fields = set(reader.fieldnames or ())
        if not required_fields.issubset(fields):
            raise ValueError(f"{path.name} must contain: {sorted(required_fields)}")
        return list(reader)


def _add_edge(graph: dict[str, set[str]], first: str, second: str) -> None:
    if first == second:
        return
    graph[first].add(second)
    graph[second].add(first)


def build_split_groups(
    manifest_rows: list[dict[str, str]],
    exact_rows: list[dict[str, str]],
    near_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Return one deterministic split-group assignment for every manifest row."""
    records = {row["record_id"]: row for row in manifest_rows}
    if len(records) != len(manifest_rows):
        raise ValueError("Manifest record_id values must be unique")

    graph: dict[str, set[str]] = defaultdict(set)
    exact_members: dict[str, list[str]] = defaultdict(list)
    for row in exact_rows:
        record_id = row["record_id"]
        if record_id not in records:
            raise ValueError(f"Exact-duplicate report references unknown record: {record_id}")
        exact_members[row["exact_duplicate_group_id"]].append(record_id)
    for members in exact_members.values():
        for record_id in members[1:]:
            _add_edge(graph, members[0], record_id)

    for row in near_rows:
        first, second = row["record_id_a"], row["record_id_b"]
        if first not in records or second not in records:
            raise ValueError(f"Near-duplicate report references unknown records: {first}, {second}")
        _add_edge(graph, first, second)

    visited: set[str] = set()
    groups: list[set[str]] = []
    for record_id in sorted(records):
        if record_id in visited:
            continue
        component: set[str] = set()
        pending = [record_id]
        while pending:
            current = pending.pop()
            if current in visited:
                continue
            visited.add(current)
            component.add(current)
            pending.extend(sorted(graph[current] - visited, reverse=True))
        groups.append(component)

    exact_edges = {
        tuple(sorted((members[0], member)))
        for members in exact_members.values()
        for member in members[1:]
    }
    near_edges = {tuple(sorted((row["record_id_a"], row["record_id_b"]))) for row in near_rows}
    assignments: list[dict[str, str]] = []
    for component in groups:
        ordered = sorted(component)
        group_digest = hashlib.sha256("\n".join(ordered).encode("utf-8")).hexdigest()[:16]
        group_id = f"split_group::{group_digest}"
        component_edges = {
            tuple(sorted((first, second)))
            for first in component
            for second in graph[first]
            if first < second and second in component
        }
        has_exact = bool(component_edges & exact_edges)
        has_near = bool(component_edges & near_edges)
        if len(component) == 1:
            reason = "singleton"
        elif has_exact and has_near:
            reason = "exact_and_likely_near_duplicate"
        elif has_exact:
            reason = "exact_duplicate"
        else:
            reason = "likely_near_duplicate"
        for record_id in ordered:
            assignments.append(
                {
                    "record_id": record_id,
                    "source_dataset": records[record_id]["source_dataset"],
                    "split_group_id": group_id,
                    "group_size": str(len(component)),
                    "group_reason": reason,
                }
            )
    return sorted(assignments, key=lambda row: row["record_id"])


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=GROUP_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--exact-duplicates", type=Path, required=True)
    parser.add_argument("--near-duplicates", type=Path, required=True)
    parser.add_argument("--groups-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    args = parser.parse_args()

    manifest_rows = _read_rows(args.manifest, {"record_id", "source_dataset"})
    exact_rows = _read_rows(args.exact_duplicates, {"exact_duplicate_group_id", "record_id"})
    near_rows = _read_rows(args.near_duplicates, {"record_id_a", "record_id_b"})
    assignments = build_split_groups(manifest_rows, exact_rows, near_rows)
    _write_csv(args.groups_output, assignments)

    group_sizes: dict[str, int] = {}
    for row in assignments:
        group_sizes[row["split_group_id"]] = int(row["group_size"])
    grouped_records = sum(size for size in group_sizes.values() if size > 1)
    summary = {
        "plan": "v2_multilabel_safe_split_groups",
        "records": len(assignments),
        "split_group_count": len(group_sizes),
        "singleton_group_count": sum(size == 1 for size in group_sizes.values()),
        "linked_record_count": grouped_records,
        "largest_group_size": max(group_sizes.values(), default=0),
        "decision": "No images were copied, moved, relabeled, or assigned to a split. A later split step must keep each split_group_id in one split.",
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Records assigned to groups: {summary['records']}")
    print(f"Safe split groups: {summary['split_group_count']}")
    print(f"Records linked to another image: {summary['linked_record_count']}")
    print(f"Largest group size: {summary['largest_group_size']}")


if __name__ == "__main__":
    main()
