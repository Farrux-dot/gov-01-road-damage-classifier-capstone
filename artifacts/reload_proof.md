# Reload Proof - GOV-01 V4

## Purpose

Demonstrate that the saved `mobilenetv2_frozen_v4.keras` model can be used outside its original training session.

## Procedure

1. Saved the locked V4 model from the original Colab training runtime.
2. Downloaded the saved model, its configuration, and one known image from the training split.
3. Deleted the original Colab runtime and connected to a fresh runtime.
4. Uploaded the saved `.keras` model and the proof image.
5. Loaded the model with `tf.keras.models.load_model(..., compile=False)` and predicted the proof image.

## Result

| Check | Original runtime | Fresh runtime after reload |
|---|---:|---:|
| Predicted label | Pothole | Pothole |
| Pothole probability | 0.907272 | 0.907272 |
| Absolute probability difference | - | 0.0 |

## Conclusion

The reload proof passed. This is a functional loading check only, not a new performance evaluation and not a reason to tune the final model.
