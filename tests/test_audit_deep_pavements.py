"""Focused checks for Deep Pavements resolution validation."""

import unittest

from src.audit_deep_pavements import is_below_minimum_resolution


class DeepPavementsAuditTests(unittest.TestCase):
    def test_accepts_exact_minimum_resolution(self) -> None:
        self.assertFalse(is_below_minimum_resolution(224, 224))

    def test_rejects_when_one_side_is_too_small(self) -> None:
        self.assertTrue(is_below_minimum_resolution(512, 223))

    def test_rejects_non_positive_dimension(self) -> None:
        with self.assertRaises(ValueError):
            is_below_minimum_resolution(0, 224)

    def test_rejects_non_positive_minimum(self) -> None:
        with self.assertRaises(ValueError):
            is_below_minimum_resolution(224, 224, minimum_side=0)


if __name__ == "__main__":
    unittest.main()
