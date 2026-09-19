import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.audit_kaggle_speed_bump import audit_dataset


class KaggleSpeedBumpAuditTests(unittest.TestCase):
    def write_image(self, path, color):
        Image.new("RGB", (16, 16), color=color).save(path)

    def test_keeps_one_duplicate_candidate_and_excludes_sequence_frames(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for label in ("bump", "crack", "potholes", "road"):
                (root / label).mkdir()

            # These two files are intentionally identical: one copy should remain usable.
            self.write_image(root / "bump" / "unique.jpg", "red")
            self.write_image(root / "bump" / "duplicate.jpg", "red")
            self.write_image(root / "bump" / "MVI_demo 001.jpg", "blue")
            self.write_image(root / "road" / "normal.jpg", "green")

            rows, report = audit_dataset(root, root)
            decisions = [row["decision"] for row in rows]

            self.assertEqual(decisions.count("keep_speed_bump_candidate"), 1)
            self.assertEqual(decisions.count("exclude_exact_duplicate_before_split"), 1)
            self.assertIn("exclude_sequence_risk", decisions)
            self.assertIn("exclude_not_speed_bump_source_label", decisions)
            self.assertEqual(report["kept_speed_bump_candidates"], 1)
            self.assertEqual(report["excluded_sequence_risk_bump_images"], 1)
            self.assertEqual(report["excluded_exact_duplicate_candidate_images"], 1)


if __name__ == "__main__":
    unittest.main()
