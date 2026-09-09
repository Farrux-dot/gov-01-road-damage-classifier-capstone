import json
import tempfile
import unittest
from pathlib import Path

from src.build_v2_manhole_crop_review import (
    build_candidates,
    load_candidate_ids,
    select_stratified_sample,
    square_crop,
)


class ManholeCropReviewTests(unittest.TestCase):
    def test_square_crop_stays_inside_image(self):
        crop = square_crop((0, 90, 20, 10), 100, 100, context_factor=2.5, minimum_side=40)
        self.assertEqual(crop, (0, 50, 50, 100))
        self.assertEqual(crop[2] - crop[0], crop[3] - crop[1])

    def test_builder_keeps_only_training_file_and_marks_risky_candidates(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            images_root = root / "data/raw/v2/svrdd/extracted/train"
            image_path = images_root / "images/Region/example.jpg"
            image_path.parent.mkdir(parents=True)
            image_path.write_bytes(b"fixture-image")
            annotation = {
                "file_name": "images/Region/example.jpg",
                "region": "Region",
                "image_id": "example",
                "width": 200,
                "height": 200,
                "objects": {
                    "v2_labels": ["manhole_cover", "manhole_cover", "crack"],
                    "bbox": [[50, 50, 30, 20], [120, 120, 30, 5], [40, 40, 60, 60]],
                },
            }
            annotations = root / "train.v2.jsonl"
            annotations.write_text(json.dumps(annotation) + "\n", encoding="utf-8")
            records = build_candidates(root, annotations, images_root)

            reserved = root / "validation.v2.jsonl"
            reserved.write_text(json.dumps(annotation) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source training"):
                build_candidates(root, reserved, images_root)

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["prefilter_status"], "hold_nearby_other_condition")
        self.assertEqual(records[1]["prefilter_status"], "hold_target_too_small")

    def test_region_balanced_selection_is_repeatable(self):
        records = []
        for region in ("A", "B", "C"):
            for index in range(4):
                records.append(
                    {
                        "candidate_id": f"{region}-{index}",
                        "region": region,
                        "prefilter_status": "review_candidate_clear_context",
                    }
                )
        first = select_stratified_sample(records, sample_size=6, seed=42)
        second = select_stratified_sample(records, sample_size=6, seed=42)
        self.assertEqual([row["candidate_id"] for row in first], [row["candidate_id"] for row in second])
        self.assertEqual({region: sum(row["region"] == region for row in first) for region in "ABC"}, {"A": 2, "B": 2, "C": 2})

    def test_round_two_selection_excludes_reviewed_and_small_candidates(self):
        records = []
        for region in ("A", "B"):
            for index, target_side in enumerate((20, 28, 36)):
                records.append(
                    {
                        "candidate_id": f"{region}-{index}",
                        "region": region,
                        "target_min_side_px": target_side,
                        "prefilter_status": "review_candidate_clear_context",
                    }
                )
        selected = select_stratified_sample(
            records,
            sample_size=2,
            seed=42,
            excluded_candidate_ids={"A-2"},
            minimum_review_target_side=28,
        )
        selected_ids = {row["candidate_id"] for row in selected}
        self.assertNotIn("A-2", selected_ids)
        self.assertTrue(all(row["target_min_side_px"] >= 28 for row in selected))
        self.assertEqual({row["region"] for row in selected}, {"A", "B"})

    def test_load_candidate_ids_validates_manifest(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            valid_manifest = root / "valid.csv"
            valid_manifest.write_text("candidate_id,decision\nA-1,approve\nA-2,reject\n", encoding="utf-8")
            self.assertEqual(load_candidate_ids(valid_manifest), {"A-1", "A-2"})

            invalid_manifest = root / "invalid.csv"
            invalid_manifest.write_text("sample_id\n1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "candidate_id"):
                load_candidate_ids(invalid_manifest)


if __name__ == "__main__":
    unittest.main()
