# GOV-01 Road Damage Image Classifier

This AI/ML capstone project classifies one submitted road image as `Normal` or `Pothole`. It supports municipal report triage only. It does **not** assess pothole danger, physical size, road safety, repair cost, or repair priority.

## Final model result

The selected model is `mobilenetv2_frozen_v4`.

- Validation Macro F1: `0.933126`
- Final protected-test Macro F1: `0.939901`
- Final protected-test accuracy: `0.950820`

See [reports/model_gate.md](reports/model_gate.md) for the full evidence, errors, limitations, and protected-test rule.

## Local Streamlit demo

The app is a local deployment route for one new road image. It loads the saved model and predicts; it never trains a model.

### Before running

1. Keep your privately downloaded model file named `mobilenetv2_frozen_v4.keras`.
2. Copy it into the local `artifacts/` folder beside `mobilenetv2_frozen_v4_config.json`.
3. Do not commit the `.keras` file or any private image to GitHub.

### Run the demo

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL displayed by Streamlit, upload a PNG or JPEG road image, and select **Classify image**.

### Smoke test

Use one known-good private image, such as your downloaded reload-proof image:

```bash
python smoke_test.py --image "C:/path/to/reload_proof_input.jpg"
```

The script checks that the saved model loads and produces a valid probability. It does not retrain the model.

## Repository structure

```text
app.py                     # Streamlit user interface
src/inference.py           # image validation, loading, and prediction logic
artifacts/                 # tracked configuration; local .keras model is ignored
smoke_test.py              # local pre-demo check
tests/test_inference.py    # small inference-logic tests
reports/model_gate.md      # model selection and final evaluation evidence
```

## Dataset documentation

The exact source, license status, download instructions, dataset size, split scheme, and limitations are documented in [data/README.md](data/README.md). Raw images are not committed to GitHub.
