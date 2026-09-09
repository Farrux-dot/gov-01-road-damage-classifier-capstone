"""Validate completed SVRDD manhole reviews and combine approved crops.

This tool reads review decision CSVs and the matching generated crop manifests.
It does not copy images, create train/validation/test splits, or train a model.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


DECISION_COLUMNS = (
    "review_round",
    "sample_id",
    "region",
    "target_min_side_px",
    "labels_in_full_image",
    "human_decision",
    "reviewer_note",
    "candidate_id",
    "source_image_path",
    "record_action",
    "evidence_flag",
)
GENERATED_COLUMNS = (
    "sample_id",
    "candidate_id",
    "source_image_id",
    "region",
    "source_image_path",
    "preview_file",
    "target_box_xywh",
    "crop_box_xyxy",
    "target_min_side_px",
    "full_image_labels",
    "nearby_non_manhole_labels",
    "proposed_label",
)
APPROVED_COLUMNS = (
    "review_round",
    "source_dataset",
    "source_split",
    "sample_id",
    "candidate_id",
    "source_image_id",
    "split_group_id",
    "region",
    "source_image_path",
    "preview_file",
    "target_box_xywh",
    "crop_box_xyxy",
    "target_min_side_px",
    "full_image_labels",
    "nearby_non_manhole_labels",
    "proposed_label",
    "human_decision",
    "reviewer_note",
    "record_action",
    "evidence_flag",
    "training_status",
)
VALID_DECISIONS = {
    "approve_manhole",
    "reject_not_manhole",
    "reject_unclear",
    "reject_mixed_condition",
    "wrong_box",
}
SOURCE_PATH_PREFIX = "data/raw/v2/svrdd/extracted/train/images/"


def load_csv(path: Path, required_columns: tuple[str, ...]) -> list[dict[str, str]]:
    """Load a CSV and retain its stripped text fields."""
    with path.open(newline="", encoding="utf-8-sig") as source_file:
        reader = csv.DictReader(source_file)
        missing = [column for column in required_columns if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path.name} is missing columns: {', '.join(missing)}")
        return [
            {column: (row.get(column) or "").strip() for column in required_columns}
            for row in reader
        ]


def validate_decision_rows(rows: list[dict[str, str]], expected_round: str) -> None:
    """Reject incomplete, unsupported, untraceable, or duplicate review rows."""
    if not rows:
        raise ValueError(f"Round {expected_round} decision manifest contains no rows")
    wrong_round = [row["sample_id"] for row in rows if row["review_round"] != expected_round]
    if wrong_round:
        raise ValueError(f"Round {expected_round} manifest contains incorrect review_round values")
    pending = [row["sample_id"] for row in rows if row["human_decision"] in {"", "pending"}]
    if pending:
        raise ValueError(f"Round {expected_round} review is incomplete: {len(pending)} pending rows")
    invalid = sorted(
        {row["human_decision"] for row in rows if row["human_decision"] not in VALID_DECISIONS}
    )
    if invalid:
        raise ValueError(f"Unsupported human_decision value(s): {', '.join(invalid)}")
    no_note = [
        row["sample_id"]
        for row in rows
        if row["human_decision"] != "approve_manhole" and not row["reviewer_note"]
    ]
    if no_note:
        raise ValueError(f"Rejected review rows require notes: {', '.join(no_note)}")
    candidate_ids = [row["candidate_id"] for row in rows]
    duplicates = sorted(key for key, count in Counter(candidate_ids).items() if count > 1)
    if duplicates:
        raise ValueError(f"Duplicate candidate_id row(s): {', '.join(duplicates)}")
    for row in rows:
        if not row["candidate_id"].startswith("svrdd::train::"):
            raise ValueError(f"Candidate is outside the SVRDD training boundary: {row['candidate_id']}")
        if not row["source_image_path"].replace("\\", "/").startswith(SOURCE_PATH_PREFIX):
            raise ValueError(f"Source path is outside the SVRDD training boundary: {row['source_image_path']}")
        try:
            if float(row["target_min_side_px"]) <= 0:
                raise ValueError
        except ValueError as error:
            raise ValueError(f"Invalid target_min_side_px for {row['candidate_id']}") from error


def index_generated_rows(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    """Index generated geometry rows and reject duplicate candidate IDs."""
    if not rows:
        raise ValueError("Generated crop manifest contains no rows")
    candidate_ids = [row["candidate_id"] for row in rows]
    duplicates = sorted(key for key, count in Counter(candidate_ids).items() if count > 1)
    if duplicates:
        raise ValueError(f"Generated manifest has duplicate candidate_id row(s): {', '.join(duplicates)}")
    return {row["candidate_id"]: row for row in rows}


def combine_approved_rows(
    review_sets: list[tuple[list[dict[str, str]], list[dict[str, str]]]],
) -> list[dict[str, str]]:
    """Join approved decisions to their crop geometry and preserve split groups."""
    all_candidate_ids: list[str] = []
    approved: list[dict[str, str]] = []
    for decisions, generated in review_sets:
        generated_by_id = index_generated_rows(generated)
        decision_ids = {row["candidate_id"] for row in decisions}
        if decision_ids != set(generated_by_id):
            missing = sorted(decision_ids - set(generated_by_id))
            unexpected = sorted(set(generated_by_id) - decision_ids)
            raise ValueError(
                "Decision/generated candidate mismatch: "
                f"missing_geometry={len(missing)}, unexpected_geometry={len(unexpected)}"
            )
        all_candidate_ids.extend(decision_ids)
        for decision in decisions:
            if decision["human_decision"] != "approve_manhole":
                continue
            geometry = generated_by_id[decision["candidate_id"]]
            if decision["source_image_path"].replace("\\", "/") != geometry["source_image_path"].replace("\\", "/"):
                raise ValueError(f"Source path mismatch for {decision['candidate_id']}")
            if decision["region"] != geometry["region"]:
                raise ValueError(f"Region mismatch for {decision['candidate_id']}")
            if abs(float(decision["target_min_side_px"]) - float(geometry["target_min_side_px"])) > 0.001:
                raise ValueError(f"Target size mismatch for {decision['candidate_id']}")
            approved.append(
                {
                    "review_round": decision["review_round"],
                    "source_dataset": "SVRDD_YOLO",
                    "source_split": "train",
                    "sample_id": decision["sample_id"],
                    "candidate_id": decision["candidate_id"],
                    "source_image_id": geometry["source_image_id"],
                    "split_group_id": f"svrdd::train::{geometry['source_image_id']}",
                    "region": decision["region"],
                    "source_image_path": decision["source_image_path"].replace("\\", "/"),
                    "preview_file": geometry["preview_file"],
                    "target_box_xywh": geometry["target_box_xywh"],
                    "crop_box_xyxy": geometry["crop_box_xyxy"],
                    "target_min_side_px": geometry["target_min_side_px"],
                    "full_image_labels": geometry["full_image_labels"],
                    "nearby_non_manhole_labels": geometry["nearby_non_manhole_labels"],
                    "proposed_label": geometry["proposed_label"],
                    "human_decision": decision["human_decision"],
                    "reviewer_note": decision["reviewer_note"],
                    "record_action": decision["record_action"],
                    "evidence_flag": decision["evidence_flag"],
                    "training_status": "approved_candidate_not_final_split",
                }
            )
    duplicates = sorted(key for key, count in Counter(all_candidate_ids).items() if count > 1)
    if duplicates:
        raise ValueError(f"Candidate IDs overlap across review rounds: {', '.join(duplicates)}")
    return sorted(approved, key=lambda row: (int(row["review_round"]), row["sample_id"]))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: tuple[str, ...]) -> None:
    """Write a deterministic UTF-8 CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for round_number in (1, 2):
        parser.add_argument(f"--round{round_number}-decisions", type=Path, required=True)
        parser.add_argument(f"--round{round_number}-generated", type=Path, required=True)
    parser.add_argument("--approved-output", type=Path, required=True)
    args = parser.parse_args()

    review_sets = []
    decision_counts: Counter[str] = Counter()
    for round_number in (1, 2):
        decisions = load_csv(getattr(args, f"round{round_number}_decisions"), DECISION_COLUMNS)
        validate_decision_rows(decisions, str(round_number))
        generated = load_csv(getattr(args, f"round{round_number}_generated"), GENERATED_COLUMNS)
        review_sets.append((decisions, generated))
        decision_counts.update(row["human_decision"] for row in decisions)

    approved = combine_approved_rows(review_sets)
    write_csv(args.approved_output, approved, APPROVED_COLUMNS)
    summary = {
        "reviewed_rows": sum(len(decisions) for decisions, _ in review_sets),
        "decision_counts": dict(sorted(decision_counts.items())),
        "approved_candidates": len(approved),
        "unique_source_images": len({row["split_group_id"] for row in approved}),
        "status": "approved_candidates_not_final_split",
    }
    print(json.dumps(summary, indent=2))
    print(f"Saved approved manifest: {args.approved_output}")


if __name__ == "__main__":
    main()
