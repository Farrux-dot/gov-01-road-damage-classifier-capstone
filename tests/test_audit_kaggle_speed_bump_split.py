import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.audit_kaggle_speed_bump_split import audit_dataset


class KaggleSpeedBumpSplitAuditTests(unittest.TestCase):
    def write_image(self, path, color):
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (16, 16), color=color).save(path)

    def test_mvi_train_frame_is_excluded_and_source_test_is_reserved(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_image(root / "train/bump/MVI_1567 001.jpg", "red")
            self.write_image(root / "train/bump/independent.jpg", "blue")
            self.write_image(root / "test/bump/MVI_1568 123.jpg", "green")

            rows, report = audit_dataset(root, root)
            decisions = {row["source_record_id"]: row["decision"] for row in rows}

        self.assertEqual(decisions["train::bump::MVI_1567 001.jpg"], "exclude_sequence_risk")
        self.assertEqual(decisions["train::bump::independent.jpg"], "keep_train_speed_bump_candidate")
        self.assertEqual(decisions["test::bump::MVI_1568 123.jpg"], "reserve_official_source_test")
        self.assertEqual(report["kept_train_speed_bump_candidates"], 1)
        self.assertEqual(report["excluded_sequence_risk_train_images"], 1)
        self.assertEqual(report["reserved_official_source_test_images"], 1)


if __name__ == "__main__":
    unittest.main()
