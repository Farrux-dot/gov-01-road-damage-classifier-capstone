from __future__ import annotations

import unittest

from src.build_v2_multilabel_split_groups import build_split_groups


class SafeSplitGroupTests(unittest.TestCase):
    def test_links_exact_and_near_duplicates_into_one_group(self):
        manifest = [
            {"record_id": "a", "source_dataset": "one"},
            {"record_id": "b", "source_dataset": "one"},
            {"record_id": "c", "source_dataset": "two"},
            {"record_id": "d", "source_dataset": "three"},
        ]
        exact = [
            {"exact_duplicate_group_id": "exact::one", "record_id": "a"},
            {"exact_duplicate_group_id": "exact::one", "record_id": "b"},
        ]
        near = [{"record_id_a": "b", "record_id_b": "c"}]

        assignments = {row["record_id"]: row for row in build_split_groups(manifest, exact, near)}

        self.assertEqual(assignments["a"]["split_group_id"], assignments["b"]["split_group_id"])
        self.assertEqual(assignments["b"]["split_group_id"], assignments["c"]["split_group_id"])
        self.assertEqual(assignments["a"]["group_size"], "3")
        self.assertEqual(assignments["a"]["group_reason"], "exact_and_likely_near_duplicate")
        self.assertEqual(assignments["d"]["group_size"], "1")
        self.assertEqual(assignments["d"]["group_reason"], "singleton")

    def test_rejects_duplicate_report_records_not_in_manifest(self):
        with self.assertRaisesRegex(ValueError, "unknown record"):
            build_split_groups(
                [{"record_id": "a", "source_dataset": "one"}],
                [],
                [{"record_id_a": "a", "record_id_b": "missing"}],
            )


if __name__ == "__main__":
    unittest.main()
