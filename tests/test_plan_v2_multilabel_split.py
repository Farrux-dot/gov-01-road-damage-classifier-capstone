from __future__ import annotations

import unittest

from src.build_v2_multilabel_coverage_manifest import ACTIVE_CONDITIONS
from src.plan_v2_multilabel_split import plan_split


def _manifest_row(record_id: str, source: str, present: set[str]) -> dict[str, str]:
    row = {"record_id": record_id, "source_dataset": source}
    for condition in ACTIVE_CONDITIONS:
        row[f"{condition}_known"] = "1" if condition in {"crack", "pothole"} else "0"
        row[f"{condition}_present"] = "1" if condition in present else ("0" if condition in {"crack", "pothole"} else "")
    return row


class MultiLabelSplitPlanTests(unittest.TestCase):
    def test_keeps_every_safe_group_in_one_planned_split(self):
        manifest = [
            _manifest_row("a", "one", {"crack"}),
            _manifest_row("b", "one", {"pothole"}),
            _manifest_row("c", "two", {"crack", "pothole"}),
            _manifest_row("d", "three", set()),
        ]
        groups = [
            {"record_id": "a", "source_dataset": "one", "split_group_id": "linked", "group_size": "2", "group_reason": "likely_near_duplicate"},
            {"record_id": "b", "source_dataset": "one", "split_group_id": "linked", "group_size": "2", "group_reason": "likely_near_duplicate"},
            {"record_id": "c", "source_dataset": "two", "split_group_id": "single-c", "group_size": "1", "group_reason": "singleton"},
            {"record_id": "d", "source_dataset": "three", "split_group_id": "single-d", "group_size": "1", "group_reason": "singleton"},
        ]

        planned, summary = plan_split(manifest, groups)
        by_id = {row["record_id"]: row for row in planned}

        self.assertEqual(by_id["a"]["planned_split"], by_id["b"]["planned_split"])
        self.assertEqual(set(by_id), {"a", "b", "c", "d"})
        self.assertEqual(summary["records"], 4)
        self.assertEqual(summary["groups"], 3)

    def test_rejects_an_unknown_label_that_is_given_a_value(self):
        row = _manifest_row("a", "one", {"crack"})
        row["road_marking_present"] = "0"
        with self.assertRaisesRegex(ValueError, "unknown road_marking"):
            plan_split(
                [row],
                [{"record_id": "a", "source_dataset": "one", "split_group_id": "single", "group_size": "1", "group_reason": "singleton"}],
            )


if __name__ == "__main__":
    unittest.main()
