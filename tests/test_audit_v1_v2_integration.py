import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.audit_v1_v2_integration import audit_cross_source_duplicates, audit_v1_training_split


def make_jpeg(path: Path, color: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 64), color=color).save(path)


class V1V2IntegrationAuditTests(unittest.TestCase):
    def test_v1_training_audit_reports_binary_labels_and_resolution(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            train = Path(temporary_directory) / "train"
            make_jpeg(train / "Normal" / "normal.jpg", "white")
            make_jpeg(train / "Pothole" / "pothole.jpg", "black")
            report, _ = audit_v1_training_split(train)
        self.assertEqual(report["class_counts"], {"Normal": 1, "Pothole": 1})
        self.assertEqual(report["resolution_counts"], {"64x64": 2})
        self.assertEqual(report["unreadable_image_count"], 0)

    def test_cross_source_audit_detects_exact_duplicate_content(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            train = root / "v1" / "train"
            shared = train / "Pothole" / "shared.jpg"
            make_jpeg(shared, "black")
            make_jpeg(train / "Normal" / "normal.jpg", "white")
            _, hashes = audit_v1_training_split(train)
            for split in ("train", "validation", "test"):
                (root / "svrdd" / split).mkdir(parents=True)
            (root / "svrdd" / "validation" / "same.jpg").write_bytes(shared.read_bytes())
            matches = audit_cross_source_duplicates(hashes, root / "svrdd")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["v1_train_paths"], ["Pothole/shared.jpg"])
