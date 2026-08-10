# Demo Fallback Evidence

## Primary route

Run the local Streamlit app with `.venv\Scripts\streamlit.exe run app.py`. The app loads the saved V1 artifact, accepts one image, and predicts. It never trains.

## If the live app is unavailable

Show this evidence in order:

1. `presentation/fallback_evidence/local_model_load_passed.png` — final saved model loaded locally.
2. `presentation/fallback_evidence/local_inference_tests_passed.png` — inference tests passed.
3. `presentation/fallback_evidence/local_streamlit_prediction.png` — local app showed `Pothole`, `96.6%`, for one road image.
4. `artifacts/reload_proof.md` and `reports/mobilenetv2_frozen_v4_reload_proof.png` — fresh-Colab reload proof.

Say: “The live app is unavailable, but this evidence shows that the saved V1 artifact loaded, the inference checks passed, and the local Streamlit interface produced a visible prediction. The output is human-review triage only.”

Do not present a screenshot as new accuracy evidence. Final performance evidence remains in `reports/model_gate.md`.
