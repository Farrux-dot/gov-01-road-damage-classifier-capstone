"""Evaluate a saved model on the held-out test set and save error-analysis artifacts."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_score, recall_score

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()
    test_dir = args.data_dir / "test"
    dataset = tf.keras.utils.image_dataset_from_directory(test_dir, image_size=IMAGE_SIZE, batch_size=BATCH_SIZE, label_mode="binary", shuffle=False)
    class_names = dataset.class_names
    y_true = np.concatenate([labels.numpy().astype(int).ravel() for _, labels in dataset])
    model = tf.keras.models.load_model(args.model_path)
    probabilities = model.predict(dataset, verbose=0).ravel()
    y_pred = (probabilities >= args.threshold).astype(int)
    metrics = {
        "threshold": args.threshold,
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "classification_report": classification_report(y_true, y_pred, target_names=class_names, output_dict=True, zero_division=0),
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/test_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    matrix = confusion_matrix(y_true, y_pred)
    sns.heatmap(matrix, annot=True, fmt="d", cmap="Blues", xticklabels=class_names, yticklabels=class_names)
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.tight_layout()
    plt.savefig("reports/confusion_matrix.png", dpi=160)
    plt.close()
    with Path("reports/test_predictions.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=("actual", "predicted", "pothole_probability", "is_error"))
        writer.writeheader()
        for actual, predicted, probability in zip(y_true, y_pred, probabilities):
            writer.writerow({"actual": class_names[actual], "predicted": class_names[predicted], "pothole_probability": round(float(probability), 6), "is_error": bool(actual != predicted)})
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
