"""Validate a completed PaveBench human review and separate its decisions.

This tool does not copy images, change source labels, build model splits, or
train a model. It only turns a fully reviewed CSV into two traceable manifests.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


REQUIRED_COLUMNS = (
    "source_category",
    "source_file",
    "source_path",
    "human_decision",
    "reviewer_note",
)
VALID_DECISIONS = {"clear_keep", "unclear_exclude"}


def load_review_rows(review_csv: Path) -> list[dict[str, str]]:
    """Load the human-review CSV and verify its required columns."""
    with review_csv.open(newline="", encoding="utf-8-sig") as review_file:
        reader = csv.DictReader(review_file)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Review CSV is missing columns: {', '.join(missing)}")
        return [{column: (row.get(column) or "").strip() for column in REQUIRED_COLUMNS} for row in reader]


def validate_review_rows(rows: list[dict[str, str]]) -> None:
    """Reject incomplete, unsupported, or duplicate human-review records."""
    if not rows:
        raise ValueError("Review CSV contains no image rows")

    pending = [row for row in rows if row["human_decision"] in {"", "pending"}]
    if pending:
        raise ValueError(f"Human review is incomplete: {len(pending)} image decisions are still pending")

    invalid = sorted({row["human_decision"] for row in rows if row["human_decision"] not in VALID_DECISIONS})
    if invalid:
        raise ValueError(f"Unsupported human_decision value(s): {', '.join(invalid)}")

    paths = [row["source_path"] for row in rows]
    duplicate_paths = sorted(path for path, count in Counter(paths).items() if count > 1)
    if duplicate_paths:
        raise ValueError(f"Duplicate source_path row(s): {', '.join(duplicate_paths)}")


def partition_review_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Return human-approved and human-excluded rows without changing them."""
    clear = [row for row in rows if row["human_decision"] == "clear_keep"]
    excluded = [row for row in rows if row["human_decision"] == "unclear_exclude"]
    return clear, excluded


def write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    """Write one decision manifest with the original traceability fields."""
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-csv", type=Path, required=True, help="Completed human_review_queue.csv file.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Ignored folder for decision manifests.")
    args = parser.parse_args()

    rows = load_review_rows(args.review_csv)
    validate_review_rows(rows)
    clear, excluded = partition_review_rows(rows)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    clear_path = args.output_dir / "clear_keep_manifest.csv"
    excluded_path = args.output_dir / "unclear_exclude_manifest.csv"
    summary_path = args.output_dir / "human_review_summary.json"
    write_manifest(clear_path, clear)
    write_manifest(excluded_path, excluded)
    summary = {
        "reviewed_image_count": len(rows),
        "clear_keep_count": len(clear),
        "unclear_exclude_count": len(excluded),
        "status": "human_review_complete",
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Saved clear manifest: {clear_path}")
    print(f"Saved excluded manifest: {excluded_path}")


if __name__ == "__main__":
    main()
