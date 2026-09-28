from __future__ import annotations

import unittest

from src.build_v2_multilabel_coverage_manifest import ACTIVE_CONDITIONS
from src.check_v2_multilabel_pre_materialization import check_pre_materialization


def _manifest(record_id: str) -> dict[str, str]:
    row = {"record_id": record_id, "source_dataset": "source", "image_reference": f"/images/{record_id}.jpg"}
    for condition in ACTIVE_CONDITIONS:
        row[f"{condition}_known"] = "1"
        row[f"{condition}_present"] = "1"
    return row


def _plan(record_id: str, split: str, group: str) -> dict[str, str]:
    return {"record_id": record_id, "source_dataset": "source", "split_group_id": group, "planned_split": split}


def _audit(record_id: str) -> dict[str, str]:
    return {"record_id": record_id, "image_reference": f"/images/{record_id}.jpg", "readable": "yes"}


class PreMaterializationCheckTests(unittest.TestCase):
    def test_accepts_complete_readable_nonleaking_plan(self):
        manifest = [_manifest(record_id) for record_id in ("a", "b", "c")]
        plan = [_plan("a", "train", "train-group"), _plan("b", "validation", "validation-group"), _plan("c", "test", "test-group")]
        coverage, summary = check_pre_materialization(manifest, plan, [_audit(record_id) for record_id in ("a", "b", "c")], [], [])

        self.assertEqual(len(coverage), 21)
        self.assertEqual(summary["status"], "pass")

    def test_rejects_near_duplicate_pair_across_splits(self):
        manifest = [_manifest(record_id) for record_id in ("a", "b", "c")]
        plan = [_plan("a", "train", "train-group"), _plan("b", "validation", "validation-group"), _plan("c", "test", "test-group")]
        with self.assertRaisesRegex(ValueError, "near-duplicate pair leaks"):
            check_pre_materialization(
                manifest,
                plan,
                [_audit(record_id) for record_id in ("a", "b", "c")],
                [],
                [{"record_id_a": "a", "record_id_b": "b"}],
            )


if __name__ == "__main__":
    unittest.main()
