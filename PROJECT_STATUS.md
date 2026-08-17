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

EXTC4 - Evidence and Defense Readiness Gate - **Yellow**

The project evidence, public demo route, local-demo evidence, and final defense deck are complete. The remaining personal preparation is to rehearse the presentation before submission or defense and record the real results honestly.

## Completed evidence

- Project scope and boundary are in `PROJECT_BRIEF.md` and `README.md`.
- V1 data audit, duplicate removal, clean split, preprocessing plan, and manifests are documented in `docs/`.
- Model-selection and protected-test evidence are in `reports/model_gate.md` and `reports/experiment_record.csv`.
- Error patterns and responsible-use boundaries are documented in `reports/error_analysis/ERROR_ANALYSIS.md` and `docs/RESPONSIBLE_AI_AND_LIMITATIONS.md`.
- The selected V1 model was saved, loaded in a fresh Colab runtime, and verified with the same proof-image probability (`0.907272`, difference `0.0`).
- The local Streamlit app ran successfully with the private model. Model-load, inference-test, and app-prediction screenshots are stored in `presentation/fallback_evidence/`.
- Local reproduction steps are in `docs/REPRODUCTION_TEST.md`.
- The final eight-slide defense deck is in `presentation/GOV_01_Road_Damage_Classifier_Defense.pptx`.

## Demo route

1. Primary route: public showcase -> [public Streamlit app](https://ff2050-gov01-road-damage.streamlit.app/) -> upload one new, non-protected road image -> **Classify image**.
2. Local verification route: run `python smoke_test.py --image <known-good-image>` and `python -m unittest discover -s tests -v` with the documented private local artifact.
3. Fallback route: show the real local evidence screenshots in `presentation/fallback_evidence/` and explain that raw data and the private local artifact are deliberately excluded from GitHub.

## V2 boundary

`experiment_dataset_v2_finetuning` is a separate experimental branch. Its protected-test result was weak, so it is closed and must not replace V1. The final assessed candidate remains V1 on `main`.

## EXTC4 evidence and defense readiness artifacts

- `docs/defense_pitch_outline.md` - complete five-minute route; personal timing remains pending.
- `docs/capstone_evidence_matrix.md` - all eight criteria, essential requirements, and three completed Show-Me-Where checks (all PASS on 2026-08-17).
- `docs/defense_question_bank.md` - ten likely questions with evidence references; personal live-answer record remains pending.
- `docs/final_action_plan.md` - exact final rehearsal actions and checks.

## Remaining finalization

1. Rehearse the final defense deck using `docs/defense_pitch_outline.md` and `presentation/SPEAKER_FLOW.md`; record actual duration and one revision.
2. Use `docs/defense_question_bank.md` and `presentation/Q_AND_A_BANK.md` to practise at least three questions and record one answer.
3. Debugging milestone completed (2026-08-15): added a Git-hygiene check and ignored the local `.venvv/` virtual-environment folder to prevent accidental commits. See `docs/AI_DEBUG_REPORT.md`.
4. After only final wording/layout corrections, freeze the repository state.
