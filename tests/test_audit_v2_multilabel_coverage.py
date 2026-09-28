from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.audit_v2_multilabel_coverage import audit_rows


class MultiLabelCoverageAuditTests(unittest.TestCase):
    def test_records_exact_duplicates_and_unreadable_images_without_changing_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = root / "first.png"
            second = root / "second.png"
            broken = root / "broken.jpg"
            Image.new("RGB", (20, 20), "white").save(first)
            second.write_bytes(first.read_bytes())
            broken.write_bytes(b"not an image")
            rows = [
                {"record_id": "a", "source_dataset": "one", "image_reference": str(first)},
                {"record_id": "b", "source_dataset": "two", "image_reference": str(second)},
                {"record_id": "c", "source_dataset": "three", "image_reference": str(broken)},
            ]
            audited, exact_rows, near_rows = audit_rows(rows)
            self.assertEqual([row["readable"] for row in audited], ["yes", "yes", "no"])
            self.assertEqual({row["record_id"] for row in exact_rows}, {"a", "b"})
            self.assertEqual(near_rows, [])
            self.assertEqual(broken.read_bytes(), b"not an image")


if __name__ == "__main__":
    unittest.main()
