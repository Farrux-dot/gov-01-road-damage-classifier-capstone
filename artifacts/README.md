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

## V2 Phase 1 multi-class E8 artifact

The final Phase 1 model selects exactly one main road condition.

| File | Purpose | Git status |
|---|---|---|
| `v2_e8_efficientnetb0_low_lr_best.keras` | Final seven-class E8 EfficientNetB0 model. Extract it from `v2_e8_output.zip`. | Ignored: generated binary. |
| `v2_multiclass_e8_config.json` | Locked class order, 224×224 input rule, and protected-test summary. | Tracked. |

- Classes: crack, manhole cover, normal asphalt, pothole, repaired road, speed bump, and unpaved road.
- Final protected-test macro F1: `0.890034` on 1,654 images.
- Use: `python -c "from src.v2_multiclass_e8_inference import predict_e8_from_artifacts; print(predict_e8_from_artifacts('road.jpg', model_path='artifacts/v2_e8_efficientnetb0_low_lr_best.keras', config_path='artifacts/v2_multiclass_e8_config.json'))"`.
- Limit: it always chooses one class, even if a scene has more than one visible condition.

## V2 Phase 2 multi-label E7 artifact

The final V2 multi-label model is a separate artifact; it does not replace the older binary demo above.

| File | Purpose | Git status |
|---|---|---|
| `e7_focused_best.keras` | Final seven-condition E7 model. Extract it from the private E7 output ZIP. | Ignored: private generated binary. |
| `v2_multilabel_e7_config.json` | Locked image size, condition order, thresholds, and final-test summary. | Tracked. |

- Input: one RGB road image resized to `320 x 320` pixels.
- Output: an independent probability for each of crack, pothole, repaired road, manhole cover, unpaved road, road marking, and speed bump.
- Thresholds: condition-specific values selected on validation before the protected test.
- Use: `python -m src.v2_multilabel_e7_inference --model-path artifacts/e7_focused_best.keras --image C:/path/to/road.jpg`.
- Limit: this is report-triage support only; human inspection remains required.
