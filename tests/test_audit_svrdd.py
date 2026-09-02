"""Focused checks for SVRDD annotation validation."""

import unittest

from src.audit_svrdd import is_valid_bbox


class SvrddAuditTests(unittest.TestCase):
    def test_accepts_tiny_source_rounding_at_image_edge(self) -> None:
        self.assertTrue(is_valid_bbox([944.001, 801.0, 80.0, 30.0], 1024, 1024))

    def test_rejects_box_meaningfully_outside_image(self) -> None:
        self.assertFalse(is_valid_bbox([1020.1, 0.0, 4.0, 10.0], 1024, 1024))

    def test_rejects_zero_size_box(self) -> None:
        self.assertFalse(is_valid_bbox([10.0, 10.0, 0.0, 10.0], 1024, 1024))


if __name__ == "__main__":
    unittest.main()
