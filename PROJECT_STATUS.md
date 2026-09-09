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

### Current V2 data-preparation experiment

- Active experimental branch: `codex/road-condition-v2`.
- PaveBench crack sample review completed on 2026-09-08: 36 images reviewed with seed `42`; 16 marked `clear_keep` and 20 marked `unclear_exclude`.
- PaveBench pothole/patch/negative sample review completed on 2026-09-08: 36 images reviewed with seed `42`; 17 marked `clear_keep` and 19 marked `unclear_exclude`.
- All 12 sampled PaveBench `pothole` images were excluded because no clear pothole was confirmed. Future V2 image-level pothole candidates will come from the 624 eligible V1 training images; V1 validation and protected-test images remain reserved.
- Eleven reviewed `patch` images remain candidates for `Repaired_road`; six reviewed `negative` images remain generic negative candidates and do not yet have specific road-condition labels.
- Data Gate decision: do not bulk-accept the PaveBench crack folders. Only individually reviewed clear images may remain candidates for a later V2 pool.
- PaveBench detection-label review completed on 2026-09-09 across 148 unique records from two review rounds. The combined evidence is documented in `docs/V2_PAVEBENCH_DETECTION_DATA_GATE.md` and `docs/v2_pavebench_detection_review_manifest.csv`.
- Detection-review results: Alligator 55/62 approved (88.7%); Crack 43/62 (69.4%); Patch 11/12 (91.7%); Pothole 4/12 (33.3%). These are human-review sample results, not model metrics or claims about every unreviewed image.
- Alligator may continue as a conditional `Crack` candidate. Crack must not be bulk-accepted. Only individually approved Patch records remain `Repaired_road` candidates. The PaveBench pothole class remains excluded; eligible V1 training pothole images remain the pothole source.
- The combined detection-review manifest contains 109 reviewed candidates and preserves two Round 1 evidence-quality flags without silently changing the original human decisions.
- No PaveBench image has been added to a combined V2 split and no V2 model has been trained from this review.
- Next small task: build one source-traceable V2 candidate inventory from eligible V1 training potholes and approved source records, while keeping generic negatives separate until they receive specific human labels.

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
