# Project Status

## Project

GOV-01 Road Damage Image Classifier

## Final assessed candidate

- Branch: `main`
- Final model: `mobilenetv2_frozen_v4`
- Task: one road image -> `Normal` or `Pothole` for human-review triage only.
- Final protected clean-test result: Macro F1 `0.939901`; accuracy `0.950820`; 183 images.
- Protected-test rule: the test result was recorded after model selection; no later tuning used the protected test set.

## Current stage

Module 8 Class 6 - Finalization and Defense Preparation - **Yellow**

The project evidence and the local-demo evidence are complete. The remaining delivery item is to create and rehearse the final defense slide deck.

## Completed evidence

- Project scope and boundary are in `PROJECT_BRIEF.md` and `README.md`.
- V1 data audit, duplicate removal, clean split, preprocessing plan, and manifests are documented in `docs/`.
- Model-selection and protected-test evidence are in `reports/model_gate.md` and `reports/experiment_record.csv`.
- Error patterns and responsible-use boundaries are documented in `reports/error_analysis/ERROR_ANALYSIS.md` and `docs/RESPONSIBLE_AI_AND_LIMITATIONS.md`.
- The selected V1 model was saved, loaded in a fresh Colab runtime, and verified with the same proof-image probability (`0.907272`, difference `0.0`).
- The local Streamlit app ran successfully with the private model. Model-load, inference-test, and app-prediction screenshots are stored in `presentation/fallback_evidence/`.
- Local reproduction steps are in `docs/REPRODUCTION_TEST.md`.

## Demo route

1. Primary route: local Streamlit app with the private `artifacts/mobilenetv2_frozen_v4.keras` model file.
2. Before demo: run `python smoke_test.py --image <known-good-image>` and `python -m unittest discover -s tests -v`.
3. Fallback route: show the real local evidence screenshots and explain that the model is deliberately excluded from GitHub.

## V2 boundary

`experiment_dataset_v2_finetuning` is a separate experimental branch. Its protected-test result was weak, so it is closed and must not replace V1. The final assessed candidate remains V1 on `main`.

## Remaining finalization

1. Create and rehearse the final defense slide deck using `presentation/DEFENSE_DECK_MAP.md` and `presentation/SPEAKER_FLOW.md`.
2. Use `presentation/Q_AND_A_BANK.md` to practise likely questions.
3. After only final wording/layout corrections, record the submission commit SHA here and freeze the repository state.
