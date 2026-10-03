"""Safe, locked single-image inference for the final GOV-01 V2 E7 model."""

from __future__ import annotations

import argparse
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, BinaryIO, Mapping

import numpy as np

from src.inference import prepare_image


@lru_cache(maxsize=2)
def load_e7_config(config_path: str | Path) -> dict[str, Any]:
    """Load and validate the tracked E7 inference configuration."""
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"E7 configuration was not found: {path}")

    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("E7 configuration is not valid JSON.") from exc

    required = {"model_file", "conditions", "input_image", "prediction_policy"}
    missing = required.difference(config)
    if missing:
        raise ValueError(f"E7 configuration is missing: {sorted(missing)}")

    conditions = config["conditions"]
    if not isinstance(conditions, list) or len(conditions) != 7:
        raise ValueError("E7 configuration must define exactly seven conditions.")
    seen_ids: set[str] = set()
    for condition in conditions:
        if not {"id", "display_name", "threshold"}.issubset(condition):
            raise ValueError("Each E7 condition needs id, display_name, and threshold.")
        condition_id = str(condition["id"])
        threshold = float(condition["threshold"])
        if condition_id in seen_ids or not 0.0 <= threshold <= 1.0:
            raise ValueError("E7 condition IDs must be unique and thresholds must be between 0 and 1.")
        seen_ids.add(condition_id)

    image_size = config["input_image"].get("image_size")
    if not isinstance(image_size, list) or len(image_size) != 2 or any(int(value) <= 0 for value in image_size):
        raise ValueError("E7 configuration has an invalid image size.")
    return config


@lru_cache(maxsize=2)
def load_e7_model(model_path: str | Path) -> Any:
    """Load E7 for inference only; compilation and training stay disabled."""
    path = Path(model_path)
    if not path.is_file():
        raise FileNotFoundError(
            f"E7 saved model was not found: {path}. "
            "Extract e7_focused_best.keras from the private E7 output ZIP into artifacts/."
        )
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise ImportError("TensorFlow is not installed. Run: python -m pip install -r requirements.txt") from exc
    return tf.keras.models.load_model(path, compile=False)


def predict_e7_image(
    image_source: str | Path | BinaryIO,
    *,
    model: Any,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Score one image using E7's locked per-condition thresholds."""
    image_size_raw = config["input_image"]["image_size"]
    image_size = (int(image_size_raw[0]), int(image_size_raw[1]))
    conditions = config["conditions"]

    image_array = prepare_image(image_source, image_size=image_size)
    batch = np.expand_dims(image_array, axis=0)
    probabilities = np.asarray(model.predict(batch, verbose=0), dtype=float)
    if probabilities.shape != (1, len(conditions)):
        raise ValueError(
            f"The saved E7 model returned shape {probabilities.shape}; expected (1, {len(conditions)})."
        )
    if not np.isfinite(probabilities).all() or ((probabilities < 0.0) | (probabilities > 1.0)).any():
        raise ValueError("The saved E7 model returned invalid probabilities.")

    scores = []
    for condition, probability in zip(conditions, probabilities[0], strict=True):
        threshold = float(condition["threshold"])
        scores.append(
            {
                "id": str(condition["id"]),
                "condition": str(condition["display_name"]),
                "probability": float(probability),
                "threshold": threshold,
                "detected": bool(probability >= threshold),
            }
        )
    return {
        "model": str(config.get("artifact_name", "E7")),
        "image_size": image_size,
        "scores": scores,
        "detected_conditions": [score["condition"] for score in scores if score["detected"]],
        "human_review_required": True,
        "operational_limit": str(config.get("operational_limit", "A human must review every prediction.")),
    }


def predict_e7_from_artifacts(
    image_source: str | Path | BinaryIO,
    *,
    model_path: str | Path,
    config_path: str | Path,
) -> dict[str, Any]:
    """Load the private E7 model and tracked config, then score one image."""
    config = load_e7_config(config_path)
    return predict_e7_image(image_source, model=load_e7_model(model_path), config=config)


def main() -> None:
    """Run one local prediction and print an easy-to-read JSON result."""
    parser = argparse.ArgumentParser(description="Run locked GOV-01 V2 E7 inference on one road image.")
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument(
        "--config-path",
        type=Path,
        default=Path("artifacts/v2_multilabel_e7_config.json"),
    )
    args = parser.parse_args()
    result = predict_e7_from_artifacts(
        args.image,
        model_path=args.model_path,
        config_path=args.config_path,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
