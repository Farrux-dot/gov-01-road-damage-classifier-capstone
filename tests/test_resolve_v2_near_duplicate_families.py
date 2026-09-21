from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from resolve_v2_near_duplicate_families import resolve, validate


def row(identifier: str, split: str) -> dict[str, str]:
    return {"candidate_id": identifier, "proposed_multiclass_label": "pothole", "split_group_id": identifier, "split": split}


class ResolutionTests(unittest.TestCase):
    def test_connected_holdout_family_becomes_train_only(self) -> None:
        pairs = [
            {"candidate_id_a": "a", "candidate_id_b": "b", "recommended_action": "holdout_required_same_visual_hash"},
            {"candidate_id_a": "b", "candidate_id_b": "c", "recommended_action": "holdout_required_likely_near_duplicate"},
            {"candidate_id_a": "a", "candidate_id_b": "d", "recommended_action": "review_required_possible_near_duplicate"},
        ]
        resolved, review = resolve([row("a", "train"), row("b", "validation"), row("c", "protected_test"), row("d", "validation")], pairs)
        validate(resolved, pairs)
        self.assertEqual({item["split"] for item in resolved[:3]}, {"train"})
        self.assertEqual(resolved[3]["split"], "validation")
        self.assertEqual(len(review), 1)


if __name__ == "__main__":
    unittest.main()
