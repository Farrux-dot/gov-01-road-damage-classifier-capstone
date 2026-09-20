"""Audit the V2 candidate inventory before any final split or model training.

This script is deliberately read-only with respect to source data.  It checks
the current inventory CSV, verifies that every referenced source image exists,
and writes a small JSON report.  It does *not* copy images, create splits, or
train a model.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    """Return a SHA-256 digest for an optional, slower integrity recheck."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_source_path(repository_root: Path, relative_path: str) -> Path:
    """Resolve an inventory path and reject paths outside the repository."""
    candidate = (repository_root / relative_path).resolve()
    try:
        candidate.relative_to(repository_root.resolve())
    except ValueError as error:
        raise ValueError(f"Inventory path is outside repository: {relative_path}") from error
    return candidate


def split_candidate(row: dict[str, str]) -> bool:
    """True only for rows that have one proposed multi-class output label."""
    return bool(row["proposed_multiclass_label"].strip()) and "multi_class" in row[
        "task_eligibility"
    ].split(";")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--verify-hashes",
        action="store_true",
        help="Recalculate every SHA-256 digest. This is slower and reads all source images.",
    )
    args = parser.parse_args()

    inventory = args.inventory.resolve()
    repository_root = inventory.parents[1]
    if not inventory.is_file():
        raise FileNotFoundError(f"Inventory not found: {inventory}")

    with inventory.open(newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))
    required = {
        "candidate_id",
        "source_id",
        "original_source_split",
        "source_image_path",
        "task_eligibility",
        "proposed_multiclass_label",
        "candidate_status",
        "sha256",
    }
    missing = required - set(rows[0] if rows else ())
    if missing:
        raise ValueError(f"Inventory is missing columns: {sorted(missing)}")

    candidate_ids = [row["candidate_id"].strip() for row in rows]
    duplicate_ids = sorted(item for item, count in Counter(candidate_ids).items() if count > 1)
    missing_files: list[str] = []
    hash_mismatches: list[str] = []
    stored_hashes: Counter[str] = Counter()
    protected_source_rows: list[str] = []
    paths_by_source: Counter[str] = Counter()

    for row in rows:
        source_path = safe_source_path(repository_root, row["source_image_path"].strip())
        paths_by_source[row["source_id"].strip()] += 1
        if not source_path.is_file():
            missing_files.append(row["candidate_id"])
            continue
        stored_hashes[row["sha256"].strip()] += 1
        source_split = row["original_source_split"].strip().lower()
        if source_split in {"validation", "val", "test", "protected_test"}:
            protected_source_rows.append(row["candidate_id"])
        if args.verify_hashes and sha256(source_path) != row["sha256"].strip():
            hash_mismatches.append(row["candidate_id"])

    split_rows = [row for row in rows if split_candidate(row)]
    no_primary_label_rows = [row for row in rows if not row["proposed_multiclass_label"].strip()]
    source_label_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in split_rows:
        source_label_counts[row["source_id"]][row["proposed_multiclass_label"]] += 1

    exact_duplicate_groups = sum(
        1 for digest, count in stored_hashes.items() if digest and count > 1
    )
    report: dict[str, Any] = {
        "audit_stage": "pre_split_final_candidate_audit",
        "inventory": inventory.relative_to(repository_root).as_posix(),
        "candidate_records": len(rows),
        "candidate_id_duplicate_count": len(duplicate_ids),
        "missing_source_image_count": len(missing_files),
        "stored_sha256_exact_duplicate_groups": exact_duplicate_groups,
        "stored_sha256_empty_count": sum(not row["sha256"].strip() for row in rows),
        "protected_source_split_rows": len(protected_source_rows),
        "hashes_recalculated": args.verify_hashes,
        "sha256_mismatch_count": len(hash_mismatches),
        "records_by_source": dict(sorted(paths_by_source.items())),
        "records_by_primary_multiclass_label": dict(
            sorted(Counter(row["proposed_multiclass_label"] for row in split_rows).items())
        ),
        "multiclass_split_candidate_records": len(split_rows),
        "non_multiclass_or_no_primary_label_records": len(no_primary_label_rows),
        "records_by_source_and_primary_label": {
            source: dict(sorted(labels.items()))
            for source, labels in sorted(source_label_counts.items())
        },
        "decision": (
            "NOT_READY_FOR_FINAL_SPLIT_OR_TRAINING: source files and exact-hash safeguards are "
            "audited, but a separate approved split-construction task must define source/image "
            "grouping, near-duplicate handling, and per-task label eligibility."
        ),
        "failures": {
            "duplicate_candidate_ids": duplicate_ids[:20],
            "missing_source_images": missing_files[:20],
            "protected_source_rows": protected_source_rows[:20],
            "sha256_mismatches": hash_mismatches[:20],
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"Candidate records: {report['candidate_records']}")
    print(f"Multi-class split candidates: {report['multiclass_split_candidate_records']}")
    print(f"Missing source images: {report['missing_source_image_count']}")
    print(f"Exact duplicate hash groups: {report['stored_sha256_exact_duplicate_groups']}")
    print(f"Protected source rows included: {report['protected_source_split_rows']}")
    print(f"Report written: {args.output}")


if __name__ == "__main__":
    main()
