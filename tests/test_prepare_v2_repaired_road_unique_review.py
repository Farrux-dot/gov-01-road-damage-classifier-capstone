"""Focused tests for repaired-road crop deduplication and quality sampling."""

import unittest

from src.prepare_v2_repaired_road_unique_review import (
    AUDIT_SUPPORTED,
    HUMAN_APPROVED,
    deduplicate_exact_crops,
    select_quality_review,
)


def crop(
    candidate_id: str,
    checksum: str,
    *,
    source_image_id: str = "image_a",
    region: str = "RegionA",
    side: int = 128,
    status: str = AUDIT_SUPPORTED,
) -> dict[str, str]:
    return {
        "candidate_id": candidate_id,
        "class_label": "repaired_road",
        "source_dataset": "SVRDD_YOLO",
        "source_split": "train",
        "source_image_id": source_image_id,
        "split_group_id": f"svrdd::train::{source_image_id}",
        "region": region,
        "source_image_path": f"data/raw/{source_image_id}.jpg",
        "materialized_image_path": f"data/processed/{candidate_id}.jpg",
        "target_box_xywh": "1,2,40,50",
        "crop_box_xyxy": f"0,0,{side},{side}",
        "target_box_in_crop_xywh": "1,2,40,50",
        "crop_width": str(side),
        "crop_height": str(side),
        "training_status": status,
        "evidence_status": "fixture",
        "output_sha256": checksum,
    }


class PrepareV2RepairedRoadUniqueReviewTests(unittest.TestCase):
    def test_exact_duplicate_prefers_human_approved_candidate(self) -> None:
        rows = [
            crop("candidate_a", "a" * 64),
            crop("candidate_b", "a" * 64, status=HUMAN_APPROVED),
        ]

        unique, excluded = deduplicate_exact_crops(rows)

        self.assertEqual([row["candidate_id"] for row in unique], ["candidate_b"])
        self.assertEqual([row["candidate_id"] for row in excluded], ["candidate_a"])
        self.assertEqual(excluded[0]["kept_candidate_id"], "candidate_b")

    def test_duplicate_crossing_source_group_is_blocked(self) -> None:
        rows = [
            crop("candidate_a", "b" * 64, source_image_id="image_a"),
            crop("candidate_b", "b" * 64, source_image_id="image_b"),
        ]

        with self.assertRaisesRegex(ValueError, "crosses a source-image split group"):
            deduplicate_exact_crops(rows)

    def test_balanced_review_is_repeatable_and_uses_unique_sources(self) -> None:
        rows: list[dict[str, str]] = []
        sizes = (128, 224, 512)
        counter = 0
        for region in ("RegionA", "RegionB"):
            for side in sizes:
                for item in range(3):
                    counter += 1
                    rows.append(
                        crop(
                            f"candidate_{counter:03d}",
                            f"{counter:064x}",
                            source_image_id=f"image_{counter:03d}",
                            region=region,
                            side=side,
                        )
                    )

        first = select_quality_review(rows, seed=42, per_region_size=2)
        second = select_quality_review(list(reversed(rows)), seed=42, per_region_size=2)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 12)
        self.assertEqual(len({row["source_image_id"] for row in first}), 12)
        self.assertTrue(all(row["human_decision"] == "pending" for row in first))

    def test_human_approved_crop_is_not_re_reviewed(self) -> None:
        rows = [
            crop(
                f"candidate_{index}",
                f"{index:064x}",
                source_image_id=f"image_{index}",
                side=128,
                status=HUMAN_APPROVED,
            )
            for index in range(3)
        ]

        with self.assertRaisesRegex(ValueError, "No audit-supported unique candidates"):
            select_quality_review(rows, seed=42, per_region_size=1)


if __name__ == "__main__":
    unittest.main()
