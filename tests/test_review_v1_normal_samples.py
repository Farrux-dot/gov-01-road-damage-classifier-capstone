import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.review_v1_normal_samples import choose_samples, image_paths, preview


class V1NormalReviewTests(unittest.TestCase):
    def test_image_paths_uses_supported_images_in_stable_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGB", (4, 4)).save(root / "b.jpg")
            Image.new("RGB", (4, 4)).save(root / "a.png")
            (root / "notes.txt").write_text("not an image", encoding="utf-8")
            self.assertEqual([path.name for path in image_paths(root)], ["a.png", "b.jpg"])

    def test_selection_is_repeatable_and_non_repeating(self):
        paths = [Path(f"normal_{index}.jpg") for index in range(10)]
        first = choose_samples(paths, 6, 42)
        second = choose_samples(paths, 6, 42)
        self.assertEqual(first, second)
        self.assertEqual(len(set(first)), 6)

    def test_selection_rejects_non_positive_count(self):
        with self.assertRaises(ValueError):
            choose_samples([Path("normal.jpg")], 0, 42)

    def test_preview_enlarges_without_smoothing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "normal.jpg"
            Image.new("RGB", (4, 4), "red").save(path)
            self.assertEqual(preview(path).size, (192, 192))


if __name__ == "__main__":
    unittest.main()
