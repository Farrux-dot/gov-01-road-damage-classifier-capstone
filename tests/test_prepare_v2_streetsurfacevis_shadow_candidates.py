"""Focused checks for the review-only StreetSurfaceVis shadow-candidate scanner."""

from __future__ import annotations

import unittest

from PIL import Image, ImageDraw

from src.prepare_v2_streetsurfacevis_shadow_candidates import ScoredImage, average_hash, hamming_distance, select_diverse, shadow_like_score


class ShadowCandidateScannerTests(unittest.TestCase):
    def test_dark_local_region_scores_higher_than_uniform_road_tone(self) -> None:
        plain = Image.new("L", (160, 160), 150)
        shaded = plain.copy()
        ImageDraw.Draw(shaded).rectangle((30, 30, 130, 130), fill=75)
        self.assertGreater(shadow_like_score(shaded), shadow_like_score(plain))

    def test_diverse_selection_keeps_near_duplicate_out(self) -> None:
        image = Image.new("L", (80, 80), 140)
        duplicate = average_hash(image)
        different = image.copy()
        ImageDraw.Draw(different).rectangle((0, 0, 39, 79), fill=20)
        selected = select_diverse([
            ScoredImage({"candidate_label": "Normal_asphalt"}, 0.9, duplicate),
            ScoredImage({"candidate_label": "Unpaved_road"}, 0.8, duplicate),
            ScoredImage({"candidate_label": "Unpaved_road"}, 0.7, average_hash(different)),
        ], maximum=3)
        self.assertEqual(len(selected), 2)
        self.assertGreater(hamming_distance(selected[0].image_hash, selected[1].image_hash), 3)

    def test_hash_distance_is_zero_for_same_image(self) -> None:
        image = Image.new("RGB", (40, 40), "gray")
        self.assertEqual(hamming_distance(average_hash(image), average_hash(image.copy())), 0)


if __name__ == "__main__":
    unittest.main()
