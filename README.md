# GOV-01 Road Damage Image Classifier

## Current V2 multi-label model

The current GOV-01 model is `E7`, which independently checks a road image for seven conditions: crack, pothole, repaired road, manhole cover, unpaved road, road marking, and speed bump.

- Final protected-test masked macro F1: `0.881724` on 3,978 expansion-test images.
- Final protected-test masked label accuracy: `0.911323`.
- Final evidence and limitations: [V2 multi-label final results](docs/V2_MULTILABEL_FINAL_RESULTS.md).
- Local one-image prediction: `python -m src.v2_multilabel_e7_inference --model-path artifacts/e7_focused_best.keras --image C:/path/to/road.jpg`.

The private `e7_focused_best.keras` file is not committed to GitHub. It must be extracted from the E7 output ZIP and kept in `artifacts/` locally. The tracked [E7 configuration](artifacts/v2_multilabel_e7_config.json) preserves its 320×320 input rule and per-condition thresholds.

## Earlier binary demo

The binary Normal/Pothole model and Streamlit demo below are retained as earlier project evidence. They are not the current V2 multi-label model.

This AI/ML capstone project classifies one submitted road image as `Normal` or `Pothole`. It supports municipal report triage only. It does **not** assess pothole danger, physical size, road safety, repair cost, or repair priority.

## Final model result

The selected model is `mobilenetv2_frozen_v4`.

- Validation Macro F1: `0.933126`
- Final protected-test Macro F1: `0.939901`
- Final protected-test accuracy: `0.950820`

See [reports/model_gate.md](reports/model_gate.md) for the full evidence, errors, limitations, and protected-test rule.

## Final review documents

- [Rubric-to-repository evidence matrix](RUBRIC_EVIDENCE_MATRIX.md)
- [Final error analysis](reports/error_analysis/ERROR_ANALYSIS.md)
- [Responsible AI and limitations](docs/RESPONSIBLE_AI_AND_LIMITATIONS.md)
- [Local demo reproduction test](docs/REPRODUCTION_TEST.md)
- [Final defense slide deck](presentation/GOV_01_Road_Damage_Classifier_Defense.pptx)
- [Defense deck map](presentation/DEFENSE_DECK_MAP.md)
- [Defense Q&A bank](presentation/Q_AND_A_BANK.md)

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

### Public Streamlit deployment

The public app downloads the final model from the public Hugging Face model repository `FF2050/gov-01-road-damage-classifier-model`. No Streamlit secret is required. The raw dataset is not included in the app or this repository.

Do not commit the `.keras` file to this GitHub repository. The app also supports the existing local route: copy the model into `artifacts/` and run Streamlit normally.

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
