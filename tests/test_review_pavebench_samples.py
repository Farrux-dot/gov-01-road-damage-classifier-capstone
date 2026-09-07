"""Focused checks for PaveBench visual-review selection."""

import tempfile
import unittest
from pathlib import Path

from src.review_pavebench_samples import REVIEW_NOTES, category_image_paths, choose_samples, display_name


class PaveBenchVisualReviewTests(unittest.TestCase):
    def test_selection_is_repeatable_and_non_repeating(self) -> None:
        candidates = [Path(f"image-{index}.jpg") for index in range(20)]
        first = choose_samples(candidates, 12, 42, "pothole")
        second = choose_samples(candidates, 12, 42, "pothole")
        self.assertEqual(first, second)
        self.assertEqual(len(set(first)), 12)

    def test_selection_rejects_non_positive_count(self) -> None:
        with self.assertRaises(ValueError):
            choose_samples([Path("image.jpg")], 0, 42, "patch")

    def test_category_paths_reads_all_source_splits(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for split in ("train", "val", "test"):
                folder = root / split / "pothole"
                folder.mkdir(parents=True)
                (folder / f"{split}.jpg").touch()
            self.assertEqual(
                {path.name for path in category_image_paths(root, "pothole")},
                {"train.jpg", "val.jpg", "test.jpg"},
            )

    def test_negative_note_prevents_automatic_specific_relabel(self) -> None:
        self.assertIn("do not relabel", REVIEW_NOTES["negative"].lower())

    def test_display_name_keeps_suffix_when_truncated(self) -> None:
        label = display_name(Path("very-long-pavebench-source-image-name-for-human-review.jpg"))
        self.assertTrue(label.endswith(".jpg"))
        self.assertIn("...", label)


if __name__ == "__main__":
    unittest.main()
