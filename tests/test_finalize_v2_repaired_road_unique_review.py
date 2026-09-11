"""Focused tests for recording the unique repaired-road quality review."""

import unittest

from src.finalize_v2_repaired_road_unique_review import (
    AUDIT_SUPPORTED,
    QUALITY_APPROVED,
    QUALITY_REJECTED,
    apply_review_decisions,
    validate_review,
)


def unique_row(candidate_id: str = "candidate_a") -> dict[str, str]:
    return {
        "candidate_id": candidate_id,
        "class_label": "repaired_road",
        "source_dataset": "SVRDD_YOLO",
        "source_split": "train",
        "source_image_id": f"image_{candidate_id}",
        "split_group_id": f"svrdd::train::image_{candidate_id}",
        "region": "Haidian",
        "source_image_path": f"data/raw/{candidate_id}.jpg",
        "materialized_image_path": f"data/processed/{candidate_id}.jpg",
        "target_box_xywh": "1,2,40,50",
        "crop_box_xyxy": "0,0,128,128",
        "target_box_in_crop_xywh": "1,2,40,50",
        "crop_width": "128",
        "crop_height": "128",
        "training_status": AUDIT_SUPPORTED,
        "evidence_status": "source_label_supported_by_100_sample_audit",
        "output_sha256": "a" * 64,
        "deduplication_status": "keep_unique_content",
        "duplicate_group_size": "1",
        "kept_candidate_id": candidate_id,
        "deduplication_reason": "only_crop_with_checksum",
    }


def review(candidate_id: str, decision: str, note: str = "") -> dict[str, str]:
    return {
        "sample_id": f"sample_{candidate_id}",
        "size_band": "small_128_191",
        "region": "Haidian",
        "crop_dimensions": "128x128",
        "candidate_id": candidate_id,
        "source_image_id": f"image_{candidate_id}",
        "split_group_id": f"svrdd::train::image_{candidate_id}",
        "materialized_image_path": f"data/processed/{candidate_id}.jpg",
        "preview_image_path": f"data/processed/previews/{candidate_id}.png",
        "training_status": AUDIT_SUPPORTED,
        "evidence_status": "source_label_supported_by_100_sample_audit",
        "proposed_label": "repaired_road",
        "human_decision": decision,
        "reviewer_note": note,
    }


class FinalizeUniqueRepairedRoadReviewTests(unittest.TestCase):
    def test_approved_candidate_becomes_human_approved(self) -> None:
        source = unique_row()
        reviews = validate_review([source], [review("candidate_a", "approve_repaired_road")])
        result = apply_review_decisions([source], reviews)
        self.assertEqual(result[0]["training_status"], QUALITY_APPROVED)
        self.assertEqual(result[0]["quality_review_status"], "reviewed_approved")

    def test_unclear_candidate_is_excluded_with_note(self) -> None:
        source = unique_row()
        reviews = validate_review(
            [source], [review("candidate_a", "reject_unclear", "Repair is not visible")]
        )
        result = apply_review_decisions([source], reviews)
        self.assertEqual(result[0]["training_status"], QUALITY_REJECTED)
        self.assertEqual(result[0]["quality_review_note"], "Repair is not visible")

    def test_rejection_without_note_is_blocked(self) -> None:
        with self.assertRaisesRegex(ValueError, "Rejected review rows require notes"):
            validate_review([unique_row()], [review("candidate_a", "reject_unclear")])

    def test_pending_review_is_blocked(self) -> None:
        with self.assertRaisesRegex(ValueError, "Review is incomplete"):
            validate_review([unique_row()], [review("candidate_a", "pending")])

    def test_unreviewed_candidate_keeps_existing_status(self) -> None:
        source = unique_row()
        result = apply_review_decisions([source], {})
        self.assertEqual(result[0]["training_status"], AUDIT_SUPPORTED)
        self.assertEqual(
            result[0]["quality_review_status"],
            "not_selected_for_unique_quality_review",
        )


if __name__ == "__main__":
    unittest.main()
