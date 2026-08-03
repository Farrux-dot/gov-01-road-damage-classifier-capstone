"""Small tests for the GOV-01 inference contract; no saved model is required."""

from __future__ import annotations

from io import BytesIO
import unittest

import numpy as np
from PIL import Image

from src.inference import predict_image, prepare_image


CONFIG = {
    "input_image": {"image_size": [224, 224]},
    "prediction_rule": {"threshold": 0.5},
    "class_mapping": {"0": "Normal", "1": "Pothole"},
}


class FixedProbabilityModel:
    """Tiny stand-in used only to test inference formatting."""

    def __init__(self, probability: float) -> None:
        self.probability = probability

    def predict(self, batch, verbose: int = 0):
        assert batch.shape == (1, 224, 224, 3)
        return np.array([[self.probability]])


def make_png() -> BytesIO:
    image = Image.new("RGBA", (20, 10), color=(10, 20, 30, 255))
    content = BytesIO()
    image.save(content, format="PNG")
    content.name = "road.png"
    content.seek(0)
    return content


class InferenceTests(unittest.TestCase):
    def test_prepare_image_converts_to_rgb_and_resizes(self) -> None:
        array = prepare_image(make_png(), image_size=(224, 224))
        self.assertEqual(array.shape, (224, 224, 3))
        self.assertEqual(array.dtype, np.float32)

    def test_prediction_uses_locked_threshold(self) -> None:
        result = predict_image(
            make_png(),
            model=FixedProbabilityModel(0.75),
            config=CONFIG,
        )
        self.assertEqual(result["label"], "Pothole")
        self.assertEqual(result["pothole_probability"], 0.75)

    def test_prediction_rejects_invalid_probability(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid probability"):
            predict_image(
                make_png(),
                model=FixedProbabilityModel(1.2),
                config=CONFIG,
            )


if __name__ == "__main__":
    unittest.main()
