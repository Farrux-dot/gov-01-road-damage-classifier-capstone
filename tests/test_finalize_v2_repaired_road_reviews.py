"""Focused tests for the repaired-road review finalizer."""

import unittest

from src.finalize_v2_repaired_road_reviews import classify_candidates, validate_reviews


def source(candidate_id: str, prefilter_status: str = "review_candidate_clear_context") -> dict[str, str]:
    image_id = candidate_id.split("::")[2]
    return {
        "candidate_id": candidate_id,
        "source_dataset": "SVRDD_YOLO",
        "source_split": "train",
        "source_image_id": image_id,
        "split_group_id": f"svrdd::train::{image_id}",
        "region": "Haidian",
        "source_image_path": f"data/raw/v2/svrdd/extracted/train/images/Haidian/{image_id}.jpg",
        "target_index": "0",
        "target_box_xywh": "1.000,2.000,40.000,50.000",
        "target_min_side_px": "40.000",
        "full_image_labels": "repaired_road",
        "nearby_other_labels": "",
        "prefilter_status": prefilter_status,
        "repaired_box_count": "1",
    }


def decision(candidate_id: str, value: str, note: str = "") -> dict[str, str]:
    image_id = candidate_id.split("::")[2]
    return {
        "review_round": "1",
        "sample_id": "repaired_001",
        "review_focus": "region_balanced_label_and_box_review",
        "region": "Haidian",
        "target_min_side_px": "40",
        "human_decision": value,
        "reviewer_note": note,
        "candidate_id": candidate_id,
        "source_image_id": image_id,
        "target_box_xywh": "1,2,40,50",
        "crop_box_xyxy": "0,0,128,128",
        "repaired_box_count": "1",
    }


class FinalizeV2RepairedRoadReviewsTests(unittest.TestCase):
    def test_approved_review_is_kept_as_human_approved(self) -> None:
        candidate_id = "svrdd::train::image_a::repaired_road::000"
        sources = [source(candidate_id)]
        reviews = [decision(candidate_id, "approve_repaired_road")]
        validated = validate_reviews(reviews, sources)
        result = classify_candidates(sources, validated)
        self.assertEqual(result[0]["training_status"], "retain_human_approved_candidate")
        self.assertEqual(result[0]["split_group_id"], "svrdd::train::image_a")

    def test_unreviewed_clear_source_label_is_not_called_human_approved(self) -> None:
        candidate_id = "svrdd::train::image_b::repaired_road::000"
        result = classify_candidates([source(candidate_id)], {})
        self.assertEqual(
            result[0]["training_status"],
            "retain_source_labeled_audit_supported_candidate",
        )
        self.assertEqual(result[0]["human_review_status"], "not_individually_reviewed")

    def test_rejected_review_is_excluded(self) -> None:
        candidate_id = "svrdd::train::image_c::repaired_road::000"
        sources = [source(candidate_id)]
        reviews = [decision(candidate_id, "reject_unclear", "Surface is not visible")]
        result = classify_candidates(sources, validate_reviews(reviews, sources))
        self.assertEqual(result[0]["training_status"], "exclude_human_rejected")

    def test_rejection_without_note_is_blocked(self) -> None:
        candidate_id = "svrdd::train::image_d::repaired_road::000"
        sources = [source(candidate_id)]
        with self.assertRaisesRegex(ValueError, "Rejected review rows require notes"):
            validate_reviews([decision(candidate_id, "wrong_box")], sources)

    def test_automatic_prefilter_hold_is_not_retained(self) -> None:
        candidate_id = "svrdd::train::image_e::repaired_road::000"
        result = classify_candidates([source(candidate_id, "hold_target_too_small")], {})
        self.assertEqual(result[0]["training_status"], "hold_target_too_small")


if __name__ == "__main__":
    unittest.main()
