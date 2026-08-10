# Local Demo Reproduction Test — V1

## Purpose

This record documents the tested local route for the final V1 model, `mobilenetv2_frozen_v4`. It is not a new model evaluation and does not change the protected-test result.

## Tested environment

- Route: local Windows Streamlit demo.
- Python: freshly created Python `3.12` virtual environment.
- TensorFlow: `2.20.0`; Keras: `3.13.2`; Streamlit: `1.60.0`.
- Required private artifact: `artifacts/mobilenetv2_frozen_v4.keras`.

The saved `.keras` file is deliberately excluded from Git. A reviewer following the local route must place their private copy beside `artifacts/mobilenetv2_frozen_v4_config.json`.

## Steps completed

1. Created a new Python 3.12 virtual environment and installed `requirements.txt`.
2. Loaded the saved V1 Keras model successfully.
3. Ran `python -m unittest discover -s tests -v`; all 3 inference-contract tests passed.
4. Started the Streamlit application with `streamlit run app.py`.
5. Uploaded one local road image and received a visible result.

## Observed result

The local app returned `Pothole` with a pothole probability of `96.6%` and instructed the user to send the report for human review. This is a known-good demonstration result, not an additional performance metric.

## Evidence

- `presentation/fallback_evidence/local_model_load_passed.png` — local model loading passed.
- `presentation/fallback_evidence/local_inference_tests_passed.png` — 3 inference-contract tests passed.
- `presentation/fallback_evidence/local_streamlit_prediction.png` — visible Streamlit prediction.
- `artifacts/reload_proof.md` — independent fresh-Colab reload proof.

## Reproduction commands

```cmd
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe smoke_test.py --image "C:\path\to\road_image.jpg"
.venv\Scripts\streamlit.exe run app.py
```

## Result and limitation

**Status: PASS for the tested local route.** The public repository cannot run the complete demo without the private `.keras` artifact. The documented fallback is the saved local artifact or the Colab reload route.
