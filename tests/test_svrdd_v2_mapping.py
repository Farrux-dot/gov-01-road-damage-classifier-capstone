import unittest

from src.svrdd_v2_mapping import (
    SVRDD_TO_V2,
    map_source_label,
    source_categories_to_multiclass,
    source_categories_to_multilabels,
)


class SvrddV2MappingTests(unittest.TestCase):
    def test_every_supported_source_label_has_the_agreed_v2_condition(self):
        self.assertEqual(set(SVRDD_TO_V2.values()), {"pothole", "crack", "manhole_cover", "repaired_road"})
        self.assertEqual(map_source_label("alligator crack"), "crack")
        self.assertEqual(map_source_label("manhole cover"), "manhole_cover")
        self.assertEqual(map_source_label("transverse patch"), "repaired_road")

    def test_unknown_source_label_is_rejected_instead_of_guessed(self):
        with self.assertRaisesRegex(ValueError, "Unsupported SVRDD source label"):
            map_source_label("shadow")

    def test_multilabels_allow_more_than_one_visible_condition(self):
        labels = source_categories_to_multilabels(["pothole", "longitudinal crack", "pothole"])
        self.assertEqual(
            labels,
            {
                "pothole_present": True,
                "crack_present": True,
                "manhole_cover_present": False,
                "repaired_road_present": False,
            },
        )

    def test_multiclass_priority_prefers_pothole_over_other_source_conditions(self):
        self.assertEqual(
            source_categories_to_multiclass(["manhole cover", "transverse patch", "pothole"]),
            "pothole",
        )


if __name__ == "__main__":
    unittest.main()
