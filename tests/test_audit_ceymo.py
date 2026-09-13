"""Focused checks for CeyMo annotation validation."""

import unittest

from src.audit_ceymo import (
    is_polygon_point_within_tolerance,
    is_valid_voc_bbox,
)


class CeymoAuditTests(unittest.TestCase):
    def test_accepts_valid_box_inside_image(self) -> None:
        self.assertTrue(is_valid_voc_bbox(10, 20, 100, 200, 1920, 1080))

    def test_rejects_box_outside_image(self) -> None:
        self.assertFalse(is_valid_voc_bbox(10, 20, 1921, 200, 1920, 1080))

    def test_rejects_zero_width_box(self) -> None:
        self.assertFalse(is_valid_voc_bbox(10, 20, 10, 200, 1920, 1080))

    def test_accepts_subpixel_polygon_boundary_rounding(self) -> None:
        self.assertTrue(is_polygon_point_within_tolerance(-0.95, 948, 1920, 1080))

    def test_rejects_meaningful_polygon_boundary_error(self) -> None:
        self.assertFalse(is_polygon_point_within_tolerance(-1.1, 948, 1920, 1080))


if __name__ == "__main__":
    unittest.main()
