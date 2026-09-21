"""Focused tests for cross-split dHash pair handling."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from audit_v2_split_near_duplicates import band_values, candidate_pairs  # noqa: E402


def record(candidate_id: str, split: str, value: int) -> dict[str, str]:
    return {
        "candidate_id": candidate_id,
        "split": split,
        "proposed_multiclass_label": "pothole",
        "source_id": "source",
        "dhash": f"{value:016x}",
        "coarse": (10, 4),
        "thumbnail": tuple([100] * 256),
    }


class V2NearDuplicateTests(unittest.TestCase):
    def test_distance_five_pair_shares_at_least_one_band(self) -> None:
        first = 0
        second = int("11111", 2)
        self.assertTrue(set(band_values(first)) & set(band_values(second)))

    def test_finds_cross_split_pair_and_ignores_same_split_pair(self) -> None:
        records = [record("train", "train", 0), record("validation", "validation", 1), record("also_train", "train", 2)]
        pairs = candidate_pairs(records, maximum_distance=1)
        self.assertEqual(len(pairs), 1)
        self.assertEqual({pairs[0]["candidate_id_a"], pairs[0]["candidate_id_b"]}, {"train", "validation"})
        self.assertEqual(pairs[0]["recommended_action"], "holdout_required_likely_near_duplicate")

    def test_distant_pair_is_not_reported(self) -> None:
        records = [record("train", "train", 0), record("test", "protected_test", (1 << 64) - 1)]
        self.assertEqual(candidate_pairs(records, maximum_distance=5), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
