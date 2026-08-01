# GOV-01 Inference Artifact

## Selected model

- **Run ID:** `mobilenetv2_frozen_v4`.
- **Task:** Binary classification of one road image as `Normal` or `Pothole`.
- **Selection evidence:** Validation Macro F1 `0.933126`.
- **Final protected-test evidence:** Macro F1 `0.939901`; accuracy `0.950820` on 183 unseen images.
- **Important limit:** This model detects pothole presence only. It does not estimate danger, size, severity, repair cost, or repair priority.

## Artifact files

| File | Purpose | Git status |
|---|---|---|
| `mobilenetv2_frozen_v4.keras` | Final saved TensorFlow/Keras model (9.19 MB when saved in Colab). | Ignored: generated binary; download and keep it privately. |
| `mobilenetv2_frozen_v4_config.json` | Input, preprocessing, class, threshold, and final-metric configuration. | Tracked. |
| `reload_proof.md` | The documented fresh-runtime reload result. | Tracked. |

## Input and prediction rule

- Input: one RGB road image, resized to `224 x 224` pixels.
- Inference preprocessing: `tf.keras.applications.mobilenet_v2.preprocess_input`.
- Output: pothole probability between 0 and 1.
- Decision threshold: probability below `0.5` means `Normal`; probability at or above `0.5` means `Pothole`.
- Class mapping: `0 = Normal`, `1 = Pothole`.
- Random flip, rotation, and zoom are **training-only**. Do not use them during prediction.

## Minimal loading example

```python
import tensorflow as tf

model = tf.keras.models.load_model("mobilenetv2_frozen_v4.keras")
image = tf.keras.utils.load_img("road_image.jpg", target_size=(224, 224))
array = tf.keras.utils.img_to_array(image)
batch = tf.expand_dims(array, axis=0)

probability = float(model.predict(batch, verbose=0)[0][0])
label = "Pothole" if probability >= 0.5 else "Normal"
print(label, probability)
```

## Runtime and reload proof

- The artifact was saved in Google Colab using TensorFlow `2.20.0`.
- The project requirements allow TensorFlow versions from `2.16` through `2.20`.
- The saved model was reloaded in a fresh Colab runtime with `compile=False`.
- A known training image produced the same `Pothole` probability before and after reload: `0.907272`.
- The absolute probability difference was `0.0`; the reload proof passed.
- See `reload_proof.md` and `reports/mobilenetv2_frozen_v4_reload_proof.png`.
