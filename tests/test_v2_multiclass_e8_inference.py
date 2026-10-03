import io
import unittest

import numpy as np
from PIL import Image

from src.v2_multiclass_e8_inference import load_e8_config, predict_e8_image


class _FakeModel:
    def __init__(self, output):
        self.output = np.asarray([output], dtype=float)

    def predict(self, batch, verbose=0):
        return self.output


class PhaseOneE8InferenceTests(unittest.TestCase):
    def setUp(self):
        self.config = load_e8_config("artifacts/v2_multiclass_e8_config.json")
        self.image = io.BytesIO()
        Image.new("RGB", (24, 24), "gray").save(self.image, format="PNG")
        self.image.name = "test_road.png"

    def test_config_keeps_the_seven_locked_classes(self):
        self.assertEqual(
            [item["id"] for item in self.config["classes"]],
            [
                "crack", "manhole_cover", "normal_asphalt", "pothole",
                "repaired_road", "speed_bump", "unpaved_road",
            ],
        )

    def test_prediction_returns_exactly_one_highest_class(self):
        result = predict_e8_image(
            self.image,
            model=_FakeModel([0.05, 0.02, 0.03, 0.71, 0.04, 0.09, 0.06]),
            config=self.config,
        )
        self.assertEqual(result["prediction"]["id"], "pothole")
        self.assertAlmostEqual(result["prediction"]["probability"], 0.71)
        self.assertEqual(len(result["scores"]), 7)

    def test_wrong_output_shape_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "expected"):
            predict_e8_image(self.image, model=_FakeModel([0.5, 0.5]), config=self.config)
