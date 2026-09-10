from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.materialize_v2_repaired_road_candidates import (
    load_keep_manifest,
    materialize,
    safe_output_name,
)


def retained_row(candidate_id: str = "svrdd::train::image_a::repaired_road::000") -> dict[str, str]:
    return {
        "candidate_id": candidate_id,
        "source_dataset": "SVRDD_YOLO",
        "source_split": "train",
        "source_image_id": "image_a",
        "split_group_id": "svrdd::train::image_a",
        "region": "Demo",
        "source_image_path": "data/raw/source.jpg",
        "target_box_xywh": "50.000,40.000,40.000,20.000",
        "training_status": "retain_human_approved_candidate",
        "evidence_status": "human_reviewed_approved",
    }


class MaterializeV2RepairedRoadCandidatesTests(unittest.TestCase):
    def test_retained_candidate_creates_traceable_rgb_crop(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_path = root / "data/raw/source.jpg"
            source_path.parent.mkdir(parents=True)
            Image.new("L", (200, 160), color=128).save(source_path)

            output_rows = materialize([retained_row()], root, root / "data/processed/crops")

            self.assertEqual(len(output_rows), 1)
            output = output_rows[0]
            self.assertEqual(output["split_group_id"], "svrdd::train::image_a")
            self.assertEqual(output["class_label"], "repaired_road")
            self.assertEqual(output["crop_width"], "128")
            self.assertEqual(output["crop_height"], "128")
            crop_path = root / output["materialized_image_path"]
            with Image.open(crop_path) as crop:
                self.assertEqual(crop.mode, "RGB")
                self.assertEqual(crop.size, (128, 128))

    def test_duplicate_candidate_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            manifest = Path(temporary_directory) / "keep.csv"
            rows = [retained_row(), retained_row()]
            with manifest.open("w", newline="", encoding="utf-8") as output_file:
                writer = csv.DictWriter(output_file, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

            with self.assertRaisesRegex(ValueError, "Duplicate candidate IDs"):
                load_keep_manifest(manifest)

    def test_source_path_outside_repository_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "repository"
            root.mkdir()
            row = retained_row()
            row["source_image_path"] = "../outside.jpg"
            Image.new("RGB", (200, 160)).save(root.parent / "outside.jpg")

            with self.assertRaisesRegex(ValueError, "outside the repository"):
                materialize([row], root, root / "data/processed/crops")

    def test_unexpected_existing_jpeg_is_not_silently_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_path = root / "data/raw/source.jpg"
            source_path.parent.mkdir(parents=True)
            Image.new("RGB", (200, 160)).save(source_path)
            output_dir = root / "data/processed/crops"
            output_dir.mkdir(parents=True)
            Image.new("RGB", (10, 10)).save(output_dir / "unrelated.jpg")

            with self.assertRaisesRegex(ValueError, "unexpected JPEG"):
                materialize([retained_row()], root, output_dir)
            self.assertTrue((output_dir / "unrelated.jpg").is_file())

    def test_output_filename_is_windows_safe_and_repeatable(self) -> None:
        candidate_id = "svrdd::train::image_a::repaired_road::000"
        first = safe_output_name(candidate_id)
        self.assertEqual(first, safe_output_name(candidate_id))
        self.assertNotIn(":", first)
        self.assertTrue(first.endswith(".jpg"))


if __name__ == "__main__":
    unittest.main()
