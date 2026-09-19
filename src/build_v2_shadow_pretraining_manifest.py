"""Build a leakage-safe SRD/ISTD shadow-pattern staging manifest.

SRD and ISTD are shadow-removal datasets. Their source-training records can
support a future shadow-pattern pretraining experiment, but they are not
automatically road-condition examples. This script does not create a V2 final
split or add records to the main road-condition inventory.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


FIELDS = (
    "staging_id",
    "audit_id",
    "source_key",
    "source_dataset",
    "source_split",
    "source_image_path",
    "width",
    "height",
    "image_sha256",
    "mask_sha256",
    "shadow_mask_coverage",
    "shadow_label",
    "road_context_status",
    "intended_use",
    "training_eligibility",
    "duplicate_decision",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def select_training_candidates(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Keep one record per exact duplicate from source-training records only."""
    eligible = [
        row
        for row in rows
        if row["source_split"] == "train"
        and row["audit_status"] == "structurally_valid_not_integrated"
    ]
    by_hash: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in eligible:
        by_hash[row["image_sha256"]].append(row)

    selected: list[dict[str, str]] = []
    duplicates_excluded = 0
    for group in by_hash.values():
        keeper = min(group, key=lambda row: row["audit_id"])
        for row in sorted(group, key=lambda item: item["audit_id"]):
            if row is not keeper:
                duplicates_excluded += 1
                continue
            selected.append(
                {
                    "staging_id": f"SHADOW_STAGE_{len(selected) + 1:05d}",
                    "audit_id": row["audit_id"],
                    "source_key": row["source_key"],
                    "source_dataset": row["source_dataset"],
                    "source_split": row["source_split"],
                    "source_image_path": row["source_image_path"],
                    "width": row["width"],
                    "height": row["height"],
                    "image_sha256": row["image_sha256"],
                    "mask_sha256": row["mask_sha256"],
                    "shadow_mask_coverage": row["shadow_mask_coverage"],
                    "shadow_label": "present_from_source_mask",
                    "road_context_status": "not_individually_road_verified",
                    "intended_use": "future_shadow_pattern_pretraining_only",
                    "training_eligibility": "blocked_pending_provenance_license_and_road_context_filter",
                    "duplicate_decision": "kept_unique_source_training_record",
                }
            )
    selected.sort(key=lambda row: row["staging_id"])
    return selected, {
        "source_training_records": len(eligible),
        "exact_duplicate_records_excluded": duplicates_excluded,
        "staged_records": len(selected),
    }


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def build(repo_root: Path) -> dict[str, object]:
    docs = repo_root / "docs"
    rows = read_csv(docs / "v2_full_shadow_source_audit_manifest.csv")
    selected, counts = select_training_candidates(rows)
    if not selected:
        raise ValueError("No structurally valid source-training shadow records found")
    write_csv(docs / "v2_shadow_pretraining_staging_manifest.csv", selected)
    return {
        **counts,
        "by_source": dict(Counter(row["source_key"] for row in selected)),
        "excluded_source_test_records": sum(row["source_split"] == "test" for row in rows),
        "main_v2_road_inventory_changed": False,
        "training_status": "blocked",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(build(args.repo_root.resolve()), indent=2))


if __name__ == "__main__":
    main()
