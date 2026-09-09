"""Focused checks for finalizing the two SVRDD manhole review rounds."""

import unittest

from src.finalize_v2_manhole_reviews import combine_approved_rows, validate_decision_rows


def decision(candidate: str, review_round: str, human_decision: str, note: str = "") -> dict[str, str]:
    image_id = candidate.split("::")[2]
    return {
        "review_round": review_round,
        "sample_id": "manhole_001",
        "region": "Chaoyang",
        "target_min_side_px": "30",
        "labels_in_full_image": "manhole_cover",
        "human_decision": human_decision,
        "reviewer_note": note,
        "candidate_id": candidate,
        "source_image_path": f"data/raw/v2/svrdd/extracted/train/images/Chaoyang/{image_id}.jpg",
        "record_action": "retain_candidate_for_v2_pool",
        "evidence_flag": "clearer_target_round2_review",
    }


def generated(candidate: str) -> dict[str, str]:
    image_id = candidate.split("::")[2]
    return {
        "sample_id": "manhole_001",
        "candidate_id": candidate,
        "source_image_id": image_id,
        "region": "Chaoyang",
        "source_image_path": f"data/raw/v2/svrdd/extracted/train/images/Chaoyang/{image_id}.jpg",
        "preview_file": "manhole_001.png",
        "target_box_xywh": "1,2,30,40",
        "crop_box_xyxy": "0,0,96,96",
        "target_min_side_px": "30",
        "full_image_labels": "manhole_cover",
        "nearby_non_manhole_labels": "",
        "proposed_label": "manhole_cover",
    }


class FinalizeV2ManholeReviewsTests(unittest.TestCase):
    def test_approved_row_keeps_geometry_and_source_split_group(self) -> None:
        candidate = "svrdd::train::image_a::manhole::001"
        rows = [decision(candidate, "2", "approve_manhole")]
        validate_decision_rows(rows, "2")
        combined = combine_approved_rows([(rows, [generated(candidate)])])
        self.assertEqual(len(combined), 1)
        self.assertEqual(combined[0]["source_image_id"], "image_a")
        self.assertEqual(combined[0]["split_group_id"], "svrdd::train::image_a")
        self.assertEqual(combined[0]["crop_box_xyxy"], "0,0,96,96")

    def test_rejected_row_is_not_added_to_approved_output(self) -> None:
        candidate = "svrdd::train::image_b::manhole::001"
        rows = [decision(candidate, "2", "reject_unclear", "Target is too dark")]
        validate_decision_rows(rows, "2")
        self.assertEqual(combine_approved_rows([(rows, [generated(candidate)])]), [])

    def test_rejected_row_without_note_is_blocked(self) -> None:
        candidate = "svrdd::train::image_c::manhole::001"
        with self.assertRaisesRegex(ValueError, "Rejected review rows require notes"):
            validate_decision_rows([decision(candidate, "2", "reject_unclear")], "2")

    def test_candidate_overlap_between_rounds_is_blocked(self) -> None:
        candidate = "svrdd::train::image_d::manhole::001"
        round1 = [decision(candidate, "1", "approve_manhole")]
        round2 = [decision(candidate, "2", "approve_manhole")]
        with self.assertRaisesRegex(ValueError, "overlap across review rounds"):
            combine_approved_rows(
                [(round1, [generated(candidate)]), (round2, [generated(candidate)])]
            )


if __name__ == "__main__":
    unittest.main()
