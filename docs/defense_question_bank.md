# Defense Question Bank - GOV-01

## Answer pattern

**Direct answer -> exact evidence -> limitation or next step.**

If unsure, state what must be verified instead of guessing.

| # | Likely defense question | Short answer | Exact evidence reference | Limitation / follow-up |
|---|---|---|---|---|
| 1 | What problem does GOV-01 solve and who uses it? | It provides an initial pothole-presence classification to help municipal staff triage road-photo reports for human review. | `PROJECT_BRIEF.md` -> "Problem and stakeholder" and "Proposed ML formulation". | It does not decide road safety, severity, repair cost, or repair priority. |
| 2 | Why did you use binary image classification? | The project needs one image to be classified as `Normal` or `Pothole`; a probability supports the human reviewer. | `PROJECT_BRIEF.md` -> "Proposed ML formulation". | The two classes do not describe every road-damage type or severity. |
| 3 | How did you prevent data leakage? | I found exact duplicate images in the supplied folders, including the supplied test folder, then rebuilt a clean stratified split from unique image hashes. | `docs/data_audit.md`; `docs/clean_image_manifest.csv`; `reports/model_gate.md` -> section 2. | Exact hashes cannot rule out visually similar scenes because no scene or location metadata was available. |
| 4 | Why did you use Macro F1? | The source data is imbalanced, so Macro F1 gives equal importance to the `Normal` and `Pothole` classes. | `reports/model_gate.md` -> section 1. | I also report per-class recall because Macro F1 alone does not show the operational risk of missed potholes. |
| 5 | What was your baseline and why is it useful? | The naive baseline predicted the majority class for every validation image and achieved Macro F1 `0.420063`. It is a minimum reference point. | `reports/experiment_record.csv` -> `naive_majority_v1`; `reports/model_gate.md` -> section 3. | It is not a useful real classifier because it gives no fair performance across both classes. |
| 6 | Why did you select MobileNetV2 V4? | It was the strongest valid validation candidate: Macro F1 `0.933126`, with correct training-only augmentation. | `reports/model_gate.md` -> sections 4-6; `reports/experiment_record.csv` -> `mobilenetv2_frozen_v4`. | The earlier V3 run is invalid because augmentation accidentally reached validation inference; V2 is a closed weak experiment. |
| 7 | What are the final results? | On the locked, protected clean test of 183 images, V4 achieved Macro F1 `0.939901` and accuracy `0.950820`. | `reports/model_gate.md` -> section 8; `reports/mobilenetv2_frozen_v4_protected_test_confusion_matrix.png`. | This test comes from the same source dataset and is not external municipal deployment validation. |
| 8 | Which model error is most serious? | Missing a pothole is more serious because it could reduce attention to a real report. The protected test had 7 missed potholes and 2 false pothole alerts. | `reports/error_analysis/ERROR_ANALYSIS.md` -> "Error types and operational impact". | The project does not prove the visual cause of each error. |
| 9 | How does the demo work? | The Streamlit app loads the saved Keras model, validates and resizes the uploaded image, then returns a label and probability. It does not train during the demo. | `app.py`; `src/inference.py`; [public Streamlit app](https://ff2050-gov01-road-damage.streamlit.app/). | A readable image can still be unlike the training data. |
| 10 | What is the main limitation or Responsible AI risk? | The model only provides preliminary triage support. A low probability must not automatically dismiss a report, because a pothole can be missed. | `docs/RESPONSIBLE_AI_AND_LIMITATIONS.md` -> "What the model must not decide" and "Required human oversight". | Real deployment would need external validation, privacy controls, access controls, and retention rules. |

## Live rehearsal question

- Question received: **Pending personal rehearsal.**
- My live answer: **Pending personal rehearsal.**
- Evidence I used: **Pending personal rehearsal.**
- What was weak / what I must verify: **Pending personal rehearsal.**
