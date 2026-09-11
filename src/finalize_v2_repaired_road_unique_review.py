"""Record the completed visual review of unique SVRDD repaired-road crops.

This tool validates the completed 60-row review against the exact
deduplicated candidate manifest. It writes separate retained and rejected
evidence manifests. It does not delete images, create final data splits, or
train a model.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


UNIQUE_COLUMNS = (
    "candidate_id",
    "class_label",
    "source_dataset",
    "source_split",
    "source_image_id",
    "split_group_id",
    "region",
    "source_image_path",
    "materialized_image_path",
    "target_box_xywh",
    "crop_box_xyxy",
    "target_box_in_crop_xywh",
    "crop_width",
    "crop_height",
    "training_status",
    "evidence_status",
    "output_sha256",
    "deduplication_status",
    "duplicate_group_size",
    "kept_candidate_id",
    "deduplication_reason",
)
REVIEW_COLUMNS = (
    "sample_id",
    "size_band",
    "region",
    "crop_dimensions",
    "candidate_id",
    "source_image_id",
    "split_group_id",
    "materialized_image_path",
    "preview_image_path",
    "training_status",
    "evidence_status",
    "proposed_label",
    "human_decision",
    "reviewer_note",
)
OUTPUT_COLUMNS = UNIQUE_COLUMNS + (
    "quality_review_status",
    "quality_review_sample_id",
    "quality_review_decision",
    "quality_review_note",
)

AUDIT_SUPPORTED = "retain_source_labeled_audit_supported_candidate"
QUALITY_APPROVED = "retain_human_approved_candidate"
QUALITY_REJECTED = "exclude_human_rejected_unique_quality"
VALID_DECISIONS = {
    "approve_repaired_road",
    "reject_not_repaired_road",
    "reject_unclear",
}


def load_csv(path: Path, required_columns: tuple[str, ...]) -> list[dict[str, str]]:
    """Load a UTF-8 CSV while preserving only the documented columns."""
    with path.open(newline="", encoding="utf-8-sig") as source_file:
        reader = csv.DictReader(source_file)
        missing = [column for column in required_columns if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path.name} is missing columns: {', '.join(missing)}")
        rows = [
            {column: (row.get(column) or "").strip() for column in required_columns}
            for row in reader
        ]
    if not rows:
        raise ValueError(f"{path.name} contains no records")
    return rows


def validate_review(
    unique_rows: list[dict[str, str]], review_rows: list[dict[str, str]]
) -> dict[str, dict[str, str]]:
    """Validate completeness and trace every review row to one unique crop."""
    pending = [
        row["sample_id"]
        for row in review_rows
        if row["human_decision"] in {"", "pending"}
    ]
    if pending:
        raise ValueError(f"Review is incomplete: {len(pending)} pending row(s)")

    invalid = sorted(
        {row["human_decision"] for row in review_rows if row["human_decision"] not in VALID_DECISIONS}
    )
    if invalid:
        raise ValueError(f"Unsupported human decision value(s): {', '.join(invalid)}")

    missing_notes = [
        row["sample_id"]
        for row in review_rows
        if row["human_decision"] != "approve_repaired_road" and not row["reviewer_note"]
    ]
    if missing_notes:
        raise ValueError(f"Rejected review rows require notes: {', '.join(missing_notes)}")

    for key in ("sample_id", "candidate_id"):
        counts = Counter(row[key] for row in review_rows)
        duplicates = sorted(value for value, count in counts.items() if count > 1)
        if duplicates:
            raise ValueError(f"Duplicate review {key}(s): {', '.join(duplicates)}")

    unique_by_id = {row["candidate_id"]: row for row in unique_rows}
    if len(unique_by_id) != len(unique_rows):
        raise ValueError("Unique manifest contains duplicate candidate IDs")

    for review in review_rows:
        candidate_id = review["candidate_id"]
        source = unique_by_id.get(candidate_id)
        if source is None:
            raise ValueError(f"Reviewed candidate is absent from the unique manifest: {candidate_id}")
        if source["training_status"] != AUDIT_SUPPORTED:
            raise ValueError(f"Reviewed candidate was not eligible for this review: {candidate_id}")

        expected = {
            "region": source["region"],
            "source_image_id": source["source_image_id"],
            "split_group_id": source["split_group_id"],
            "materialized_image_path": source["materialized_image_path"],
            "crop_dimensions": f"{source['crop_width']}x{source['crop_height']}",
            "proposed_label": source["class_label"],
        }
        for field, expected_value in expected.items():
            if review[field] != expected_value:
                raise ValueError(f"{field} mismatch for {candidate_id}")

    return {row["candidate_id"]: row for row in review_rows}


def apply_review_decisions(
    unique_rows: list[dict[str, str]], reviews_by_id: dict[str, dict[str, str]]
) -> list[dict[str, str]]:
    """Apply reviewed decisions while preserving unreviewed candidate status."""
    output: list[dict[str, str]] = []
    for source in unique_rows:
        review = reviews_by_id.get(source["candidate_id"])
        row = {column: source.get(column, "") for column in UNIQUE_COLUMNS}

        if review is None:
            row.update(
                {
                    "quality_review_status": "not_selected_for_unique_quality_review",
                    "quality_review_sample_id": "",
                    "quality_review_decision": "",
                    "quality_review_note": "",
                }
            )
        elif review["human_decision"] == "approve_repaired_road":
            row.update(
                {
                    "training_status": QUALITY_APPROVED,
                    "evidence_status": "human_reviewed_approved_unique_quality",
                    "quality_review_status": "reviewed_approved",
                    "quality_review_sample_id": review["sample_id"],
                    "quality_review_decision": review["human_decision"],
                    "quality_review_note": review["reviewer_note"],
                }
            )
        else:
            row.update(
                {
                    "training_status": QUALITY_REJECTED,
                    "evidence_status": "human_reviewed_rejected_unique_quality",
                    "quality_review_status": "reviewed_rejected",
                    "quality_review_sample_id": review["sample_id"],
                    "quality_review_decision": review["human_decision"],
                    "quality_review_note": review["reviewer_note"],
                }
            )
        output.append(row)
    return sorted(output, key=lambda row: row["candidate_id"])


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    """Write a deterministic UTF-8 evidence manifest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unique-manifest", type=Path, required=True)
    parser.add_argument("--review-manifest", type=Path, required=True)
    parser.add_argument("--keep-output", type=Path, required=True)
    parser.add_argument("--exclude-output", type=Path, required=True)
    args = parser.parse_args()

    unique_rows = load_csv(args.unique_manifest, UNIQUE_COLUMNS)
    review_rows = load_csv(args.review_manifest, REVIEW_COLUMNS)
    reviews_by_id = validate_review(unique_rows, review_rows)
    classified = apply_review_decisions(unique_rows, reviews_by_id)
    kept = [row for row in classified if row["training_status"] != QUALITY_REJECTED]
    excluded = [row for row in classified if row["training_status"] == QUALITY_REJECTED]
    write_csv(args.keep_output, kept)
    write_csv(args.exclude_output, excluded)

    summary = {
        "unique_candidates_before_quality_review": len(classified),
        "review_rows": len(review_rows),
        "review_decisions": dict(
            sorted(Counter(row["human_decision"] for row in review_rows).items())
        ),
        "retained_unique_candidates": len(kept),
        "excluded_unclear_candidates": len(excluded),
        "retained_training_statuses": dict(
            sorted(Counter(row["training_status"] for row in kept).items())
        ),
        "files_deleted": 0,
        "final_split_created": False,
        "model_trained": False,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
