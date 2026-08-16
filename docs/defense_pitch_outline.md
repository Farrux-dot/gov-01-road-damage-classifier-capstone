# Defense Pitch Outline - GOV-01

## Five-minute route

| Time | Block | My exact line / evidence route |
|---|---|---|
| 0:00-0:30 | Opening | "My project is GOV-01 Road Damage Image Classifier. Municipal staff can receive many road photos, so the system gives a first `Normal` or `Pothole` classification to support human review. It does not make repair or safety decisions." Evidence: `PROJECT_BRIEF.md` -> "Problem and stakeholder". |
| 0:30-1:15 | User and ML task | "The intended user is municipal staff reviewing road-condition reports. The input is one RGB road image. The output is a pothole probability and a `Normal` or `Pothole` label." Evidence: `PROJECT_BRIEF.md` -> "Proposed ML formulation". |
| 1:15-2:10 | Data and approach | "I used the documented Kaggle road-image dataset. The supplied folders contained exact duplicates, including in the supplied test data, so I rebuilt a clean stratified 70/15/15 split from 1,228 unique labelled images. I compared a naive majority rule, a compact CNN, a class-weighted CNN, and frozen MobileNetV2. The final candidate was selected using validation Macro F1, not the protected test." Evidence: `docs/data_audit.md`; `reports/model_gate.md` -> sections 2-6. |
| 2:10-3:10 | Results and weakness | "The selected `mobilenetv2_frozen_v4` achieved Macro F1 `0.939901` and accuracy `0.950820` on 183 protected clean-test images. The validation Macro F1 of the simple CNN baseline was `0.673898`, while the final model achieved `0.933126`. On the protected test, the final model missed 7 potholes and made 2 false pothole alerts. A missed pothole is the more serious error, so human review remains required." Evidence: `reports/model_gate.md` -> sections 3, 8, and 9; `reports/error_analysis/ERROR_ANALYSIS.md` -> "Confusion-matrix interpretation". |
| 3:10-4:20 | Showcase and live demo | Open [the public showcase](https://farrux-dot.github.io/gov-01-road-damage-classifier-capstone/) -> select **Open Live Demo** -> upload one new road image to [the public Streamlit app](https://ff2050-gov01-road-damage.streamlit.app/) -> select **Classify image** -> read the predicted label and pothole probability -> state that the result is only for human review. Do not use a protected-test image as a demo example. |
| 4:20-5:00 | Close and question | "The model detects possible pothole presence only. It does not determine danger, physical size, severity, repair priority, repair cost, or road safety. A future improvement is a separate external evaluation with higher-resolution and more geographically diverse images, including difficult negative cases." Then invite one question and use: Decision -> exact evidence -> limitation or next step. |

## Demo route

- Showcase entry: [GOV-01 static showcase](https://farrux-dot.github.io/gov-01-road-damage-classifier-capstone/)
- Live demo entry: [GOV-01 Streamlit app](https://ff2050-gov01-road-damage.streamlit.app/)
- One real input -> output example: upload one non-protected road image -> select **Classify image** -> read the `Normal` or `Pothole` result and probability -> remind the audience that a human must review it.
- Backup screenshot/link (rehearsal fallback only): `presentation/fallback_evidence/local_streamlit_prediction.png`; `presentation/FALLBACK_EVIDENCE.md`.

## Rehearsal log

- Actual duration: **Pending personal timed rehearsal.**
- Question received: **Pending.**
- My live answer: **Pending.**
- Answer weakness / what I must verify: use exact evidence locations rather than saying "in the notebook" or "the app works".
- One pitch revision before defense: **Pending after the first timed rehearsal.**
