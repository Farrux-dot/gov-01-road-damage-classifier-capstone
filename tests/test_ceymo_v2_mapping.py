"""Focused checks for the CeyMo-to-V2 road-marking mapping."""

import unittest

from src.ceymo_v2_mapping import (
    CEYMO_LABEL_NAMES,
    map_ceymo_label,
    road_marking_present,
)


class CeymoV2MappingTests(unittest.TestCase):
    def test_all_official_source_labels_map_to_road_marking(self) -> None:
        mapped = {map_ceymo_label(label) for label in CEYMO_LABEL_NAMES}
        self.assertEqual(mapped, {"road_marking"})

    def test_multiple_source_markings_produce_one_positive_condition(self) -> None:
        self.assertTrue(road_marking_present(["SA", "PC"]))

    def test_empty_annotation_is_not_a_positive_condition(self) -> None:
        self.assertFalse(road_marking_present([]))

    def test_unknown_source_label_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported CeyMo label"):
            map_ceymo_label("pothole")


if __name__ == "__main__":
    unittest.main()
