"""Focused checks for RAD YOLO row validation."""

import unittest

from src.audit_rad import parse_yolo_row


class RadAuditTests(unittest.TestCase):
    def test_accepts_valid_unsurfaced_road_row(self) -> None:
        self.assertEqual(parse_yolo_row("5 0.5 0.5 0.8 0.4"), 5)

    def test_rejects_invalid_zero_width(self) -> None:
        self.assertIsNone(parse_yolo_row("5 0.5 0.5 0.0 0.4"))

    def test_rejects_unknown_class(self) -> None:
        self.assertIsNone(parse_yolo_row("6 0.5 0.5 0.2 0.2"))

    def test_rejects_out_of_range_coordinate(self) -> None:
        self.assertIsNone(parse_yolo_row("5 1.1 0.5 0.2 0.2"))


if __name__ == "__main__":
    unittest.main()
