"""Run safe single-image inference for the GOV-01 demo."""
from __future__ import annotations

import argparse
from pathlib import Path

import tensorflow as tf

VALID_SUFFIXES = {".jpg", ".jpeg", ".png"}
IMAGE_SIZE = (224, 224)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()
    if not args.image.is_file() or args.image.suffix.lower() not in VALID_SUFFIXES:
        raise ValueError("Please provide a readable JPG, JPEG, or PNG image.")
    image = tf.keras.utils.load_img(args.image, target_size=IMAGE_SIZE)
    batch = tf.expand_dims(tf.keras.utils.img_to_array(image), axis=0)
    probability = float(tf.keras.models.load_model(args.model_path).predict(batch, verbose=0)[0][0])
    label = "Pothole" if probability >= args.threshold else "Normal"
    confidence = probability if label == "Pothole" else 1 - probability
    print(f"Prediction: {label}")
    print(f"Confidence: {confidence:.1%}")
    print("Use this output only to support report triage; a human inspector must confirm road condition.")


if __name__ == "__main__":
    main()
