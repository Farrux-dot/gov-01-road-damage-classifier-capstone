"""Run a quick local check of the saved GOV-01 deployment artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.inference import predict_from_artifacts


ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "artifacts" / "mobilenetv2_frozen_v4.keras"
CONFIG_PATH = ROOT / "artifacts" / "mobilenetv2_frozen_v4_config.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check that the saved GOV-01 model loads and predicts one image."
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Path to one readable PNG, JPG, or JPEG image.",
    )
    args = parser.parse_args()

    result = predict_from_artifacts(
        args.image,
        model_path=MODEL_PATH,
        config_path=CONFIG_PATH,
    )

    print("SMOKE TEST PASSED")
    print("Prediction:", result["label"])
    print("Pothole probability:", f"{result['pothole_probability']:.6f}")


if __name__ == "__main__":
    main()
