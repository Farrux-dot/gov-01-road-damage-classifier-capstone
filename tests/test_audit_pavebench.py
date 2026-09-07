"""Focused checks for PaveBench COCO-box validation."""

import unittest

from src.audit_pavebench import is_valid_coco_bbox


class PaveBenchAuditTests(unittest.TestCase):
    def test_accepts_box_at_image_edge(self) -> None:
        self.assertTrue(is_valid_coco_bbox([400, 300, 112, 212], 512, 512))

    def test_rejects_box_outside_image(self) -> None:
        self.assertFalse(is_valid_coco_bbox([500, 0, 13, 20], 512, 512))

    def test_rejects_non_positive_box(self) -> None:
        self.assertFalse(is_valid_coco_bbox([10, 10, 0, 20], 512, 512))


if __name__ == "__main__":
    unittest.main()
