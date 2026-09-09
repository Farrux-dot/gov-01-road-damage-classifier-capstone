"""Finalize audited SVRDD repaired-road candidates from two human reviews.

This tool uses only the SVRDD source-training annotations. It validates the
review decisions, applies the documented automatic prefilter, and writes
traceable keep and exclude manifests. It does not create final data splits,
copy images, or train a model.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


DECISION_COLUMNS = (
    "review_round",
    "sample_id",
    "review_focus",
    "region",
    "target_min_side_px",
    "human_decision",
    "reviewer_note",
    "candidate_id",
    "source_image_id",
    "target_box_xywh",
    "crop_box_xyxy",
    "repaired_box_count",
)
OUTPUT_COLUMNS = (
    "candidate_id",
    "source_dataset",
    "source_split",
    "source_image_id",
    "split_group_id",
    "region",
    "source_image_path",
    "target_index",
    "target_box_xywh",
    "target_min_side_px",
    "full_image_labels",
    "nearby_other_labels",
    "prefilter_status",
    "human_review_status",
    "review_round",
    "review_focus",
    "human_decision",
    "reviewer_note",
    "training_status",
    "evidence_status",
)
VALID_DECISIONS = {
    "approve_repaired_road",
    "reject_not_repaired_road",
    "reject_unclear",
    "reject_incomplete_boxes",
    "wrong_box",
    "wrong_target_box",
}
MIN_TARGET_SIDE = 28.0
SOURCE_PREFIX = "data/raw/v2/svrdd/extracted/train/"


def load_csv(path: Path, required_columns: tuple[str, ...]) -> list[dict[str, str]]:
    """Load required columns from a UTF-8 CSV and strip surrounding spaces."""
    with path.open(newline="", encoding="utf-8-sig") as source_file:
        reader = csv.DictReader(source_file)
        missing = [column for column in required_columns if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path.name} is missing columns: {', '.join(missing)}")
        return [
            {column: (row.get(column) or "").strip() for column in required_columns}
            for row in reader
        ]


def parse_box(text: str) -> tuple[float, float, float, float]:
    """Parse four comma-separated box coordinates."""
    values = tuple(float(value.strip()) for value in text.split(","))
    if len(values) != 4:
        raise ValueError(f"Expected four box values, found: {text}")
    return values  # type: ignore[return-value]


def square_crop(
    box: tuple[float, float, float, float],
    width: int,
    height: int,
    factor: float = 2.5,
    minimum: int = 128,
) -> tuple[int, int, int, int]:
    """Return the same contextual square used by the first review prefilter."""
    x, y, box_width, box_height = box
    side = min(max(int(round(max(box_width, box_height) * factor)), minimum), width, height)
    center_x, center_y = x + box_width / 2, y + box_height / 2
    left = max(0, min(int(round(center_x - side / 2)), width - side))
    top = max(0, min(int(round(center_y - side / 2)), height - side))
    return left, top, left + side, top + side


def overlap_area(
    box: tuple[float, float, float, float], crop: tuple[int, int, int, int]
) -> float:
    """Calculate the pixel area shared by one object box and one crop."""
    x, y, width, height = box
    left, top, right, bottom = crop
    return max(0.0, min(x + width, right) - max(x, left)) * max(
        0.0, min(y + height, bottom) - max(y, top)
    )


def build_source_candidates(annotation_path: Path) -> list[dict[str, str]]:
    """Build all repaired-road box records from the source training annotations."""
    candidates: list[dict[str, str]] = []
    with annotation_path.open(encoding="utf-8") as source_file:
        for line in source_file:
            item: dict[str, Any] = json.loads(line)
            labels = item["objects"]["v2_labels"]
            boxes = [tuple(map(float, box)) for box in item["objects"]["bbox"]]
            repaired_count = sum(label == "repaired_road" for label in labels)
            for index, (label, box) in enumerate(zip(labels, boxes)):
                if label != "repaired_road":
                    continue
                target_min_side = min(box[2], box[3])
                crop = square_crop(box, int(item["width"]), int(item["height"]))
                crop_area = max((crop[2] - crop[0]) * (crop[3] - crop[1]), 1)
                nearby: set[str] = set()
                for other_index, (other_label, other_box) in enumerate(zip(labels, boxes)):
                    if other_index == index or other_label == "repaired_road":
                        continue
                    shared = overlap_area(other_box, crop)
                    other_area = max(other_box[2] * other_box[3], 1.0)
                    if shared / other_area >= 0.10 or shared / crop_area >= 0.02:
                        nearby.add(other_label)
                if target_min_side < MIN_TARGET_SIDE:
                    prefilter_status = "hold_target_too_small"
                elif nearby:
                    prefilter_status = "hold_nearby_other_condition"
                else:
                    prefilter_status = "review_candidate_clear_context"
                image_id = str(item["image_id"])
                candidates.append(
                    {
                        "candidate_id": f"svrdd::train::{image_id}::repaired_road::{index:03d}",
                        "source_dataset": "SVRDD_YOLO",
                        "source_split": "train",
                        "source_image_id": image_id,
                        "split_group_id": f"svrdd::train::{image_id}",
                        "region": str(item["region"]),
                        "source_image_path": f"{SOURCE_PREFIX}{item['file_name']}",
                        "target_index": str(index),
                        "target_box_xywh": ",".join(f"{value:.3f}" for value in box),
                        "target_min_side_px": f"{target_min_side:.3f}",
                        "full_image_labels": ";".join(sorted(set(labels))),
                        "nearby_other_labels": ";".join(sorted(nearby)),
                        "prefilter_status": prefilter_status,
                        "repaired_box_count": str(repaired_count),
                    }
                )
    candidate_ids = [row["candidate_id"] for row in candidates]
    duplicates = sorted(key for key, count in Counter(candidate_ids).items() if count > 1)
    if duplicates:
        raise ValueError(f"Duplicate source candidate IDs: {', '.join(duplicates)}")
    return candidates


def validate_reviews(
    decisions: list[dict[str, str]], candidates: list[dict[str, str]]
) -> dict[str, dict[str, str]]:
    """Validate that decisions are complete and match unchanged source geometry."""
    if not decisions:
        raise ValueError("Review decision manifest contains no rows")
    pending = [row["sample_id"] for row in decisions if row["human_decision"] in {"", "pending"}]
    if pending:
        raise ValueError(f"Review is incomplete: {len(pending)} pending rows")
    invalid = sorted(
        {row["human_decision"] for row in decisions if row["human_decision"] not in VALID_DECISIONS}
    )
    if invalid:
        raise ValueError(f"Unsupported human_decision value(s): {', '.join(invalid)}")
    missing_notes = [
        row["sample_id"]
        for row in decisions
        if row["human_decision"] != "approve_repaired_road" and not row["reviewer_note"]
    ]
    if missing_notes:
        raise ValueError(f"Rejected review rows require notes: {', '.join(missing_notes)}")
    decision_ids = [row["candidate_id"] for row in decisions]
    duplicates = sorted(key for key, count in Counter(decision_ids).items() if count > 1)
    if duplicates:
        raise ValueError(f"Duplicate reviewed candidate IDs: {', '.join(duplicates)}")

    source_by_id = {row["candidate_id"]: row for row in candidates}
    for decision in decisions:
        candidate_id = decision["candidate_id"]
        source = source_by_id.get(candidate_id)
        if source is None:
            raise ValueError(f"Reviewed candidate is outside SVRDD training annotations: {candidate_id}")
        if source["prefilter_status"] != "review_candidate_clear_context":
            raise ValueError(f"Reviewed candidate did not pass the prefilter: {candidate_id}")
        if decision["source_image_id"] != source["source_image_id"]:
            raise ValueError(f"Source image ID mismatch for {candidate_id}")
        if decision["region"] != source["region"]:
            raise ValueError(f"Region mismatch for {candidate_id}")
        if abs(float(decision["target_min_side_px"]) - float(source["target_min_side_px"])) > 0.01:
            raise ValueError(f"Target size mismatch for {candidate_id}")
        reviewed_box = parse_box(decision["target_box_xywh"])
        source_box = parse_box(source["target_box_xywh"])
        if any(abs(left - right) > 0.01 for left, right in zip(reviewed_box, source_box)):
            raise ValueError(f"Target box mismatch for {candidate_id}")
        if decision["repaired_box_count"] and int(decision["repaired_box_count"]) != int(
            source["repaired_box_count"]
        ):
            raise ValueError(f"Repaired-box count mismatch for {candidate_id}")
    return {row["candidate_id"]: row for row in decisions}


def classify_candidates(
    candidates: list[dict[str, str]], decisions_by_id: dict[str, dict[str, str]]
) -> list[dict[str, str]]:
    """Add review and evidence status without claiming a final training split."""
    output: list[dict[str, str]] = []
    for candidate in candidates:
        decision = decisions_by_id.get(candidate["candidate_id"])
        if candidate["prefilter_status"] == "hold_target_too_small":
            training_status = "hold_target_too_small"
            evidence_status = "automated_prefilter_hold"
        elif candidate["prefilter_status"] == "hold_nearby_other_condition":
            training_status = "hold_nearby_other_condition"
            evidence_status = "automated_prefilter_hold"
        elif decision and decision["human_decision"] != "approve_repaired_road":
            training_status = "exclude_human_rejected"
            evidence_status = "human_reviewed_rejected"
        elif decision:
            training_status = "retain_human_approved_candidate"
            evidence_status = "human_reviewed_approved"
        else:
            training_status = "retain_source_labeled_audit_supported_candidate"
            evidence_status = "source_label_supported_by_100_sample_audit"

        output.append(
            {
                **{column: candidate.get(column, "") for column in OUTPUT_COLUMNS},
                "human_review_status": (
                    "not_individually_reviewed"
                    if decision is None
                    else (
                        "reviewed_approved"
                        if decision["human_decision"] == "approve_repaired_road"
                        else "reviewed_rejected"
                    )
                ),
                "review_round": decision["review_round"] if decision else "",
                "review_focus": decision["review_focus"] if decision else "",
                "human_decision": decision["human_decision"] if decision else "",
                "reviewer_note": decision["reviewer_note"] if decision else "",
                "training_status": training_status,
                "evidence_status": evidence_status,
            }
        )
    return sorted(output, key=lambda row: row["candidate_id"])


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    """Write a deterministic UTF-8 CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--all-output", type=Path, required=True)
    parser.add_argument("--keep-output", type=Path, required=True)
    parser.add_argument("--exclude-output", type=Path, required=True)
    args = parser.parse_args()

    candidates = build_source_candidates(args.annotations)
    decisions = load_csv(args.decisions, DECISION_COLUMNS)
    decisions_by_id = validate_reviews(decisions, candidates)
    classified = classify_candidates(candidates, decisions_by_id)
    kept = [row for row in classified if row["training_status"].startswith("retain_")]
    excluded = [row for row in classified if not row["training_status"].startswith("retain_")]
    write_csv(args.all_output, classified)
    write_csv(args.keep_output, kept)
    write_csv(args.exclude_output, excluded)

    summary = {
        "source_repaired_road_boxes": len(classified),
        "prefilter_counts": dict(sorted(Counter(row["prefilter_status"] for row in classified).items())),
        "review_decisions": dict(sorted(Counter(row["human_decision"] for row in decisions).items())),
        "training_status_counts": dict(
            sorted(Counter(row["training_status"] for row in classified).items())
        ),
        "kept_candidates": len(kept),
        "excluded_or_held_candidates": len(excluded),
        "source_splits_used": sorted({row["source_split"] for row in classified}),
        "final_split_created": False,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
