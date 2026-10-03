"""Locked single-image inference for the GOV-01 V2 Phase 1 E8 model."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, BinaryIO, Mapping

import numpy as np

from src.inference import prepare_image


@lru_cache(maxsize=2)
def load_e8_config(config_path: str | Path) -> dict[str, Any]:
    """Load the configuration that fixes E8's class order and input rule."""
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Phase 1 E8 configuration was not found: {path}")
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Phase 1 E8 configuration is not valid JSON.") from exc

    required = {"model_file", "classes", "input_image", "prediction_policy"}
    missing = required.difference(config)
    if missing:
        raise ValueError(f"Phase 1 E8 configuration is missing: {sorted(missing)}")

    classes = config["classes"]
    if not isinstance(classes, list) or len(classes) != 7:
        raise ValueError("Phase 1 E8 configuration must define exactly seven classes.")
    ids = [str(item.get("id", "")) for item in classes]
    if len(set(ids)) != len(ids) or not all(ids):
        raise ValueError("Phase 1 E8 class IDs must be present and unique.")
    if not all(str(item.get("display_name", "")) for item in classes):
        raise ValueError("Phase 1 E8 classes need display names.")

    image_size = config["input_image"].get("image_size")
    if not isinstance(image_size, list) or len(image_size) != 2 or any(int(value) <= 0 for value in image_size):
        raise ValueError("Phase 1 E8 configuration has an invalid image size.")
    return config


@lru_cache(maxsize=2)
def load_e8_model(model_path: str | Path) -> Any:
    """Load E8 for inference without compiling or changing it."""
    path = Path(model_path)
    if not path.is_file():
        raise FileNotFoundError(f"Phase 1 E8 model was not found: {path}")
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise ImportError("TensorFlow is not installed. Run: python -m pip install -r requirements.txt") from exc
    return tf.keras.models.load_model(path, compile=False)


def predict_e8_image(
    image_source: str | Path | BinaryIO,
    *,
    model: Any,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Choose exactly one Phase 1 class for an image."""
    raw_size = config["input_image"]["image_size"]
    image_size = (int(raw_size[0]), int(raw_size[1]))
    classes = config["classes"]
    image_array = prepare_image(image_source, image_size=image_size)
    probabilities = np.asarray(model.predict(np.expand_dims(image_array, axis=0), verbose=0), dtype=float)

    if probabilities.shape != (1, len(classes)):
        raise ValueError(
            f"Phase 1 E8 returned shape {probabilities.shape}; expected (1, {len(classes)})."
        )
    if not np.isfinite(probabilities).all() or ((probabilities < 0.0) | (probabilities > 1.0)).any():
        raise ValueError("Phase 1 E8 returned invalid probabilities.")

    selected_index = int(np.argmax(probabilities[0]))
    scores = [
        {
            "id": str(item["id"]),
            "condition": str(item["display_name"]),
            "probability": float(probability),
        }
        for item, probability in zip(classes, probabilities[0], strict=True)
    ]
    selected = scores[selected_index]
    return {
        "model": str(config.get("artifact_name", "Phase 1 E8")),
        "image_size": image_size,
        "prediction": selected,
        "scores": scores,
        "human_review_required": True,
        "operational_limit": str(config.get("operational_limit", "A human must review every prediction.")),
    }


def predict_e8_from_artifacts(
    image_source: str | Path | BinaryIO,
    *,
    model_path: str | Path,
    config_path: str | Path,
) -> dict[str, Any]:
    """Load the locked E8 artifacts and predict one image."""
    config = load_e8_config(config_path)
    return predict_e8_image(image_source, model=load_e8_model(model_path), config=config)
