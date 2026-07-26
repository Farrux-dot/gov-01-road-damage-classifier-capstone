"""Train either a baseline CNN or a MobileNetV2 transfer-learning classifier."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import tensorflow as tf

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 42


def load_data(data_dir: Path):
    train_dir = data_dir / "train"
    val_dir = next((data_dir / name for name in ("val", "valid", "validation") if (data_dir / name).exists()), None)
    test_dir = data_dir / "test"
    if val_dir is None or not train_dir.exists() or not test_dir.exists():
        raise FileNotFoundError("Expected train, val/valid/validation, and test folders in --data-dir.")
    common = dict(image_size=IMAGE_SIZE, batch_size=BATCH_SIZE, label_mode="binary", seed=SEED)
    train = tf.keras.utils.image_dataset_from_directory(train_dir, shuffle=True, **common)
    val = tf.keras.utils.image_dataset_from_directory(val_dir, shuffle=False, **common)
    test = tf.keras.utils.image_dataset_from_directory(test_dir, shuffle=False, **common)
    return train, val, test


def make_model(kind: str) -> tf.keras.Model:
    augmentation = tf.keras.Sequential([
        tf.keras.layers.RandomFlip("horizontal"),
        tf.keras.layers.RandomRotation(0.08),
        tf.keras.layers.RandomZoom(0.10),
        tf.keras.layers.RandomContrast(0.10),
    ], name="augmentation")
    if kind == "baseline_cnn":
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(*IMAGE_SIZE, 3)), augmentation,
            tf.keras.layers.Rescaling(1 / 255.0),
            tf.keras.layers.Conv2D(32, 3, activation="relu"), tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(64, 3, activation="relu"), tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(128, 3, activation="relu"), tf.keras.layers.GlobalAveragePooling2D(),
            tf.keras.layers.Dropout(0.3), tf.keras.layers.Dense(1, activation="sigmoid"),
        ])
    else:
        base = tf.keras.applications.MobileNetV2(include_top=False, weights="imagenet", input_shape=(*IMAGE_SIZE, 3))
        base.trainable = False
        inputs = tf.keras.Input(shape=(*IMAGE_SIZE, 3))
        x = augmentation(inputs)
        x = tf.keras.applications.mobilenet_v2.preprocess_input(x)
        x = base(x, training=False)
        x = tf.keras.layers.GlobalAveragePooling2D()(x)
        x = tf.keras.layers.Dropout(0.25)(x)
        outputs = tf.keras.layers.Dense(1, activation="sigmoid")(x)
        model = tf.keras.Model(inputs, outputs, name="mobilenetv2_classifier")
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy", tf.keras.metrics.Precision(name="precision"), tf.keras.metrics.Recall(name="recall"), tf.keras.metrics.AUC(name="roc_auc")])
    return model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--model", choices=("baseline_cnn", "mobilenetv2"), required=True)
    parser.add_argument("--epochs", type=int, default=12)
    args = parser.parse_args()
    tf.keras.utils.set_random_seed(SEED)
    train, val, _ = load_data(args.data_dir)
    autotune = tf.data.AUTOTUNE
    train, val = train.prefetch(autotune), val.prefetch(autotune)
    model = make_model(args.model)
    Path("models").mkdir(exist_ok=True)
    Path("reports").mkdir(exist_ok=True)
    callbacks = [tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True)]
    history = model.fit(train, validation_data=val, epochs=args.epochs, callbacks=callbacks)
    model.save(Path("models") / f"{args.model}.keras")
    Path("reports") .joinpath(f"{args.model}_history.json").write_text(json.dumps(history.history, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
