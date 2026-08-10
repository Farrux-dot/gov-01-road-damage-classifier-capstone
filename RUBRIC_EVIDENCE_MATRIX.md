# Rubric-to-Repository Evidence Matrix

This is the reviewer map for the GOV-01 Road Damage Image Classifier. It points to Version 1 (V1), the final assessed model. Version 2 (V2) is a separate, closed experiment and is not the final demo candidate.

## Status key

- **Green** — evidence is present and has a clear explanation.
- **Yellow** — substantial evidence exists, but one named finalization item remains.
- **Red** — a minimum submission requirement is missing or broken.

| Criterion | Max | Status | Exact evidence | Named finalization item |
|---|---:|---|---|---|
| 1. Problem definition and alignment | 10 | Green | `PROJECT_BRIEF.md`; `README.md`; this matrix | None identified. |
| 2. Data and preprocessing pipeline | 15 | Green | `data/README.md`; `docs/data_audit.md`; `docs/clean_image_manifest.csv`; `docs/split_summary.csv`; `docs/preprocessing_manifest.json`; `notebooks/GOV_01_data_preprocessing.ipynb` | None identified. |
| 3. Modeling and experiments | 20 | Green | `docs/modeling_readiness.md`; V1 model notebooks; `reports/experiment_record.csv`; `reports/model_gate.md` | V1 remains final; V2 stays separate and closed. |
| 4. Evaluation and error analysis | 15 | Green | `reports/model_gate.md`; `reports/error_analysis/ERROR_ANALYSIS.md`; V4 confusion-matrix images; `reports/experiment_record.csv` | None identified. |
| 5. End-to-end delivery | 20 | Green | `app.py`; `src/inference.py`; `smoke_test.py`; `tests/test_inference.py`; `artifacts/README.md`; `docs/REPRODUCTION_TEST.md`; `presentation/fallback_evidence/` | Private `.keras` artifact remains outside Git. |
| 6. Documentation and reproducibility | 10 | Green | `README.md`; `requirements.txt`; `data/README.md`; `artifacts/README.md`; `docs/REPRODUCTION_TEST.md` | Local route requires the documented private artifact. |
| 7. Responsible AI and limitations | 5 | Green | `docs/RESPONSIBLE_AI_AND_LIMITATIONS.md`; `PROJECT_BRIEF.md`; `data/README.md`; `reports/error_analysis/ERROR_ANALYSIS.md` | None identified. |
| 8. Presentation, demo, and Q&A | 5 | Yellow | `presentation/DEFENSE_DECK_MAP.md`; `presentation/SPEAKER_FLOW.md`; `presentation/Q_AND_A_BANK.md`; `presentation/FALLBACK_EVIDENCE.md`; local Streamlit route | Create and rehearse the final defense slide deck. |

## Essential passing checks

| Requirement | Current evidence | Status |
|---|---|---|
| Student-trained or fine-tuned model | `mobilenetv2_frozen_v4` training and selection in `reports/model_gate.md` | Green |
| Final model evaluated on unseen data | Protected clean-test Macro F1 `0.939901`; accuracy `0.950820` | Green |
| Working end-to-end demo route | Local model-load, test, and Streamlit screenshots in `presentation/fallback_evidence/` | Green |
| Clear reproduction instructions | `README.md` and `docs/REPRODUCTION_TEST.md` | Green |
| Explainable defense package | Evidence map, speaker flow, fallback, and Q&A are in `presentation/` | Yellow — final slide deck and rehearsal remain. |

## Final model boundary

- **Final model:** `mobilenetv2_frozen_v4` trained on the V1 clean split.
- **Final protected test:** Macro F1 `0.939901`; accuracy `0.950820`; 183 images.
- **Allowed claim:** preliminary `Normal` or `Pothole` triage support for human review.
- **Not allowed claim:** no decision about danger, size, severity, repair priority, repair cost, or legal road safety.
- **V2 boundary:** V2 is closed after a weak protected-test result; it must not replace V1 or be described as deployable.

## Remaining finalization order

1. Create and rehearse the final defense slide deck using `presentation/DEFENSE_DECK_MAP.md`.
2. Review only final corrections, record the final commit SHA in `PROJECT_STATUS.md`, and freeze the submission state.
