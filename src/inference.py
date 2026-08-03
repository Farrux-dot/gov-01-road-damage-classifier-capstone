"""Loading, validation, and prediction functions for the GOV-01 demo."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, BinaryIO, Mapping

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError


ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png"}


@lru_cache(maxsize=2)
def load_artifact_config(config_path: str | Path) -> dict[str, Any]:
    """Load the tracked configuration needed to use the saved model safely."""
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Model configuration was not found: {path}")

    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Model configuration is not valid JSON.") from exc

    required_keys = {"class_mapping", "input_image", "prediction_rule"}
    missing = required_keys.difference(config)
    if missing:
        raise ValueError(f"Model configuration is missing: {sorted(missing)}")
    return config


@lru_cache(maxsize=2)
def load_saved_model(model_path: str | Path) -> Any:
    """Load the final Keras artifact without compiling or retraining it."""
    path = Path(model_path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Saved model was not found: {path}. "
            "Copy mobilenetv2_frozen_v4.keras into artifacts/."
        )
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise ImportError(
            "TensorFlow is not installed. Run: python -m pip install -r requirements.txt"
        ) from exc
    return tf.keras.models.load_model(path, compile=False)


def prepare_image(
    image_source: str | Path | BinaryIO,
    *,
    image_size: tuple[int, int],
) -> np.ndarray:
    """Validate one image and return an RGB batch-ready array.

    The saved Keras model already contains MobileNetV2 inference preprocessing.
    This function therefore only validates, converts to RGB, and resizes.
    """
    source_name = getattr(image_source, "name", "uploaded image")
    suffix = Path(str(source_name)).suffix.lower()
    if suffix and suffix not in ALLOWED_SUFFIXES:
        raise ValueError("Use a PNG, JPG, or JPEG road image.")

    try:
        if hasattr(image_source, "seek"):
            image_source.seek(0)
        with Image.open(image_source) as opened_image:
            image = ImageOps.exif_transpose(opened_image).convert("RGB")
            if image.width < 1 or image.height < 1:
                raise ValueError("The uploaded image has invalid dimensions.")
            resized = image.resize(image_size)
            array = np.asarray(resized, dtype=np.float32)
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("The selected file is not a readable image.") from exc

    if array.shape != (image_size[1], image_size[0], 3):
        raise ValueError("The image could not be converted to the expected RGB format.")
    return array


def predict_image(
    image_source: str | Path | BinaryIO,
    *,
    model: Any,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the locked model's label and pothole probability for one image."""
    raw_size = config["input_image"]["image_size"]
    image_size = (int(raw_size[0]), int(raw_size[1]))
    threshold = float(config["prediction_rule"]["threshold"])

    image_array = prepare_image(image_source, image_size=image_size)
    batch = np.expand_dims(image_array, axis=0)
    probability = float(np.ravel(model.predict(batch, verbose=0))[0])

    if not 0.0 <= probability <= 1.0:
        raise ValueError("The saved model returned an invalid probability.")

    label = "Pothole" if probability >= threshold else "Normal"
    return {
        "label": label,
        "pothole_probability": probability,
        "threshold": threshold,
        "image_size": image_size,
    }


def predict_from_artifacts(
    image_source: str | Path | BinaryIO,
    *,
    model_path: str | Path,
    config_path: str | Path,
) -> dict[str, Any]:
    """Load the locked artifacts and predict one image without retraining."""
    config = load_artifact_config(config_path)
    model = load_saved_model(model_path)
    return predict_image(image_source, model=model, config=config)
