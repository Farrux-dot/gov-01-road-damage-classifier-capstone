"""Create a conservative, metadata-only V2 near-duplicate resolution plan.

Distance-0--3 pairs, plus distance-4--5 pairs confirmed by visual review, are
treated as one connected visual family. Each family is moved to training so no
member remains in validation or the protected test. Families whose members
have conflicting labels are excluded rather than relabeled.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


def holdout_pair(pair: dict[str, str]) -> bool:
    return pair["recommended_action"].startswith("holdout_required") or pair.get("decision") == "confirmed_exact_duplicate"


def families(pairs: list[dict[str, str]]) -> list[list[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    for pair in pairs:
        if holdout_pair(pair):
            graph[pair["candidate_id_a"]].add(pair["candidate_id_b"])
            graph[pair["candidate_id_b"]].add(pair["candidate_id_a"])
    seen: set[str] = set()
    result: list[list[str]] = []
    for start in sorted(graph):
        if start in seen:
            continue
        stack, component = [start], []
        seen.add(start)
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbour in graph[current]:
                if neighbour not in seen:
                    seen.add(neighbour)
                    stack.append(neighbour)
        result.append(sorted(component))
    return result


def family_id(members: list[str]) -> str:
    digest = hashlib.sha256("\n".join(members).encode("utf-8")).hexdigest()[:16]
    return f"near_duplicate_family::{digest}"


def resolve(manifest: list[dict[str, str]], pairs: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    by_id = {row["candidate_id"]: row for row in manifest}
    if len(by_id) != len(manifest):
        raise ValueError("Manifest candidate IDs must be unique")
    assignment: dict[str, str] = {}
    conflicts: set[str] = set()
    for members in families(pairs):
        labels = {by_id[member]["proposed_multiclass_label"] for member in members}
        if len(labels) != 1:
            conflicts.update(members)
        identifier = family_id(members)
        for member in members:
            assignment[member] = identifier
    resolved = []
    for row in manifest:
        item = dict(row)
        item["original_split"] = row["split"]
        item["near_duplicate_family_id"] = assignment.get(row["candidate_id"], "")
        item["near_duplicate_resolution"] = "exclude_label_conflict" if item["candidate_id"] in conflicts else ("train_only_holdout_family" if item["near_duplicate_family_id"] else "no_holdout_family")
        if item["near_duplicate_family_id"]:
            item["split_group_id"] = item["near_duplicate_family_id"]
            item["split"] = "excluded_label_conflict" if item["candidate_id"] in conflicts else "train"
        resolved.append(item)
    review = [pair for pair in pairs if not holdout_pair(pair)]
    return resolved, review


def validate(resolved: list[dict[str, str]], pairs: list[dict[str, str]]) -> None:
    by_id = {row["candidate_id"]: row for row in resolved}
    for pair in pairs:
        if holdout_pair(pair) and by_id[pair["candidate_id_a"]]["split"] != by_id[pair["candidate_id_b"]]["split"]:
            raise ValueError("Holdout pair still crosses a split")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--pairs", type=Path, required=True)
    parser.add_argument("--resolved-manifest", type=Path, required=True)
    parser.add_argument("--review-queue", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    with args.manifest.open(newline="", encoding="utf-8-sig") as handle:
        manifest = list(csv.DictReader(handle))
    with args.pairs.open(newline="", encoding="utf-8-sig") as handle:
        pairs = list(csv.DictReader(handle))
    resolved, review = resolve(manifest, pairs)
    validate(resolved, pairs)
    fields = list(manifest[0]) + ["original_split", "near_duplicate_family_id", "near_duplicate_resolution"]
    for path, rows, row_fields in ((args.resolved_manifest, resolved, fields), (args.review_queue, review, list(pairs[0]))):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=row_fields)
            writer.writeheader(); writer.writerows(rows)
    report = {"policy": "confirmed_near_duplicate_families_train_only_with_label_conflicts_excluded", "manifest_status": "proposed_not_materialized", "records": len(resolved), "holdout_family_count": len(families(pairs)), "holdout_record_count": sum(bool(row["near_duplicate_family_id"]) for row in resolved), "remaining_review_pair_count": len(review), "split_counts": dict(Counter(row["split"] for row in resolved))}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
