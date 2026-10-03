"""Tests for result routing; they do not load TensorFlow models."""

import unittest

from src.app_logic import select_result_view


class ResultViewTests(unittest.TestCase):
    def test_zero_or_one_e7_detection_uses_one_condition_view(self):
        self.assertEqual(select_result_view([]), "one_condition")
        self.assertEqual(select_result_view(["Pothole"]), "one_condition")

    def test_two_or_more_e7_detections_use_multiple_conditions_view(self):
        self.assertEqual(select_result_view(["Pothole", "Crack"]), "multiple_conditions")


if __name__ == "__main__":
    unittest.main()
