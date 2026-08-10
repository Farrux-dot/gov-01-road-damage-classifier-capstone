# Rubric-to-Repository Evidence Matrix

This document is the reviewer map for the GOV-01 Road Damage Image Classifier. It points to the current Version 1 (V1) evidence only. Version 2 (V2) is a separate, closed experiment and is **not** the final model or demo candidate.

## Status key

- **Green** — evidence is present and the criterion has a clear explanation.
- **Yellow** — substantial evidence exists, but a named finalization item remains.
- **Red** — a minimum submission requirement is missing or broken.

## Assessment evidence

| Criterion | Max | Current status | Exact evidence | Named finalization item |
|---|---:|---|---|---|
| 1. Problem definition and alignment | 10 | Green | `PROJECT_BRIEF.md`; `README.md` | Add this matrix to the final reviewer route. |
| 2. Data and preprocessing pipeline | 15 | Green | `data/README.md`; `docs/data_audit.md`; `docs/clean_image_manifest.csv`; `docs/split_summary.csv`; `docs/preprocessing_manifest.json`; `notebooks/GOV_01_data_preprocessing.ipynb` | None identified in this evidence map. |
| 3. Modeling and experiments | 20 | Green | `docs/modeling_readiness.md`; `notebooks/GOV_01_model_gate.ipynb`; `notebooks/GOV_01_class_weighted_cnn.ipynb`; `notebooks/GOV_01_mobilenetv2_transfer_v4.ipynb`; `reports/experiment_record.csv`; `reports/model_gate.md` | Clearly label V1 as final and V2 as a closed non-deployable experiment. |
| 4. Evaluation and error analysis | 15 | Yellow | `reports/model_gate.md`; `reports/mobilenetv2_frozen_v4_protected_test_confusion_matrix.png`; `reports/mobilenetv2_frozen_v4_validation_confusion_matrix.png`; `reports/experiment_record.csv` | Create one short final error-analysis document that explains the false-positive and false-negative risks. |
| 5. End-to-end delivery | 20 | Yellow | `app.py`; `src/inference.py`; `smoke_test.py`; `tests/test_inference.py`; `artifacts/README.md`; `artifacts/reload_proof.md` | Record the known-good local app result and one fallback item in the repository. The private `.keras` artifact remains outside Git. |
| 6. Documentation and reproducibility | 10 | Yellow | `README.md`; `requirements.txt`; `data/README.md`; `artifacts/README.md`; `artifacts/reload_proof.md` | Create a final clean-reproduction test record for the local demo route. |
| 7. Responsible AI and limitations | 5 | Yellow | `PROJECT_BRIEF.md`; `data/README.md`; `reports/model_gate.md`; `artifacts/README.md` | Create one project-specific responsible-use and limitations document. |
| 8. Presentation, demo, and Q&A | 5 | Yellow | `README.md`; `PROJECT_STATUS.md`; local Streamlit route | Create the defense map, speaker flow, fallback checklist, and Q&A bank. |

## Essential passing checks

| Requirement | Current evidence | Status |
|---|---|---|
| Student-trained or fine-tuned ML model | `mobilenetv2_frozen_v4` selection and training evidence in `reports/model_gate.md` | Green |
| Final model evaluated on unseen data | Protected clean test Macro F1 `0.939901` and accuracy `0.950820` in `reports/model_gate.md` | Green |
| Working end-to-end demo route | Local Streamlit code, inference tests, and smoke-test script are present | Yellow — final local-run record still needed |
| Clear reproduction instructions | README, requirements, data access, and artifact loading instructions are present | Yellow — fresh local-demo reproduction record still needed |
| Explainable defense package | Core evidence exists across the repository | Yellow — defense materials still need to be created |

## Final model boundary

- **Final assessed model:** `mobilenetv2_frozen_v4` trained on the Version 1 clean split.
- **Final protected-test result:** Macro F1 `0.939901`; accuracy `0.950820`; 183 protected clean test images.
- **Allowed claim:** the system gives a preliminary `Normal` or `Pothole` image-classification result to support human report triage.
- **Not allowed claim:** it does not assess danger, pothole size, severity, repair priority, repair cost, or legal road safety.
- **V2 boundary:** the Rome-road V2 experiment is closed after a weak protected-test result. It must not replace V1 or be described as deployable.

## Finalization order

1. Add final error analysis and responsible-use documentation.
2. Record the clean local-demo reproduction test and fallback evidence.
3. Create defense map, speaker flow, and Q&A bank.
4. Update README and `PROJECT_STATUS.md` to point to this final evidence.
5. Review the repository, make final corrections only, and freeze the final commit.
