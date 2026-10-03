"""Tests for the E7 multi-label inference contract; no saved model is required."""

from __future__ import annotations

from io import BytesIO
import unittest

import numpy as np
from PIL import Image

from src.v2_multilabel_e7_inference import load_e7_config, predict_e7_image


CONFIG_PATH = "artifacts/v2_multilabel_e7_config.json"


class FixedE7Model:
    """Small stand-in that proves shape and threshold handling without TensorFlow."""

    def __init__(self, probabilities: list[float]) -> None:
        self.probabilities = probabilities

    def predict(self, batch, verbose: int = 0):
        assert batch.shape == (1, 320, 320, 3)
        return np.asarray([self.probabilities], dtype=float)


def make_image() -> BytesIO:
    image = Image.new("RGBA", (14, 9), color=(12, 34, 56, 255))
    content = BytesIO()
    image.save(content, format="PNG")
    content.name = "road.png"
    content.seek(0)
    return content


class E7InferenceTests(unittest.TestCase):
    def test_config_has_locked_e7_thresholds(self) -> None:
        config = load_e7_config(CONFIG_PATH)
        self.assertEqual(config["input_image"]["image_size"], [320, 320])
        self.assertEqual(len(config["conditions"]), 7)
        self.assertEqual(config["conditions"][1]["threshold"], 0.46)

    def test_prediction_reports_each_condition_and_detection(self) -> None:
        result = predict_e7_image(
            make_image(),
            model=FixedE7Model([0.46, 0.45, 0.56, 0.48, 0.71, 0.49, 0.50]),
            config=load_e7_config(CONFIG_PATH),
        )
        self.assertEqual(result["image_size"], (320, 320))
        self.assertEqual(len(result["scores"]), 7)
        self.assertEqual(result["detected_conditions"], ["Crack", "Repaired road", "Unpaved road", "Speed bump"])
        self.assertTrue(result["human_review_required"])

    def test_prediction_rejects_wrong_model_output_shape(self) -> None:
        with self.assertRaisesRegex(ValueError, "returned shape"):
            predict_e7_image(
                make_image(),
                model=FixedE7Model([0.5]),
                config=load_e7_config(CONFIG_PATH),
            )


if __name__ == "__main__":
    unittest.main()
