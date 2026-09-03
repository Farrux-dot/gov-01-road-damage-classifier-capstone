import unittest

from src.review_svrdd_samples import choose_samples, display_name, records_by_category


def record(name, categories):
    return {"file_name": name, "objects": {"categories": categories}}


class SvrddVisualReviewTests(unittest.TestCase):
    def test_groups_a_record_once_per_category(self):
        grouped = records_by_category([record("road.jpg", [3, 3, 4])])
        self.assertEqual([item["file_name"] for item in grouped[3]], ["road.jpg"])
        self.assertEqual([item["file_name"] for item in grouped[4]], ["road.jpg"])

    def test_selection_is_repeatable_and_has_no_repeated_images(self):
        candidates = [record(f"road-{index}.jpg", [3]) for index in range(10)]
        first = choose_samples(candidates, 6, 42, 3)
        second = choose_samples(candidates, 6, 42, 3)
        self.assertEqual([item["file_name"] for item in first], [item["file_name"] for item in second])
        self.assertEqual(len({item["file_name"] for item in first}), 6)

    def test_selection_rejects_non_positive_count(self):
        with self.assertRaises(ValueError):
            choose_samples([record("road.jpg", [3])], 0, 42, 3)

    def test_display_name_removes_source_folder_and_truncates_long_name(self):
        label = display_name("images/Fengtai/very-long-source-image-name-for-review.jpg")
        self.assertNotIn("images/", label)
        self.assertTrue(label.endswith("..."))


if __name__ == "__main__":
    unittest.main()
