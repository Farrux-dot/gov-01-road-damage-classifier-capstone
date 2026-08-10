# GOV-01 Defense Q&A Bank

Use: **Decision -> Evidence -> Limitation.**

## Why did you choose this ML task?

**Decision:** Binary image classification gives a first pothole-presence indication for report triage.<br>
**Evidence:** `PROJECT_BRIEF.md`.<br>
**Limitation:** It does not estimate severity, safety, or repair priority.

## How did you prevent data leakage?

**Decision:** I rebuilt a clean split from unique image hashes.<br>
**Evidence:** `docs/data_audit.md` records 140 duplicate groups and duplicate supplied test images; `docs/clean_image_manifest.csv` documents the clean split.<br>
**Limitation:** no scene or location metadata exists, so exact hashes cannot rule out every visually similar scene.

## Why did you use Macro F1?

**Decision:** Macro F1 gives equal importance to both imbalanced classes.<br>
**Evidence:** `docs/data_audit.md` and `reports/model_gate.md`.<br>
**Limitation:** class-specific recall and operational risk must also be checked.

## What was your baseline?

**Decision:** The baseline predicted the majority class for every validation image.<br>
**Evidence:** `reports/experiment_record.csv` records Macro F1 `0.420063`.<br>
**Limitation:** it cannot identify both classes fairly.

## Why was MobileNetV2 V4 selected?

**Decision:** Corrected frozen MobileNetV2 V4 was selected after validation comparison.<br>
**Evidence:** validation Macro F1 `0.933126` in `reports/model_gate.md`.<br>
**Limitation:** V3 was invalid because validation images were randomly augmented by mistake.

## What are the final results?

**Decision:** I evaluated the locked V4 candidate once on a protected clean test.<br>
**Evidence:** Macro F1 `0.939901`, accuracy `0.950820`, 183 images, in `reports/model_gate.md`.<br>
**Limitation:** this is not proof of performance in every city or road condition.

## Which error is most costly?

**Decision:** Missing a pothole is more serious because it could reduce attention to a genuine report.<br>
**Evidence:** 7 missed potholes and 2 false alerts in `reports/error_analysis/ERROR_ANALYSIS.md`.<br>
**Limitation:** no individual visual cause was proven for each error.

## How does the demo work without training?

**Decision:** Streamlit loads a saved Keras artifact and calls reusable inference code.<br>
**Evidence:** `app.py`, `src/inference.py`, `artifacts/README.md`.<br>
**Limitation:** the `.keras` artifact is private and must be supplied locally.

## What happens with invalid input?

**Decision:** The code accepts readable PNG, JPG, or JPEG images and converts them to RGB.<br>
**Evidence:** `src/inference.py`; `tests/test_inference.py`.<br>
**Limitation:** a valid file may still be unlike the training data.

## Who could be harmed by a wrong output?

**Decision:** Road users and municipal staff could be affected if a classification is treated as a safety or repair decision.<br>
**Evidence:** `docs/RESPONSIBLE_AI_AND_LIMITATIONS.md`.<br>
**Limitation:** this project is not a municipal deployment study.

## How can another person reproduce the demo?

**Decision:** They follow the local instructions, add their private saved artifact, run tests, and run Streamlit.<br>
**Evidence:** `README.md`; `docs/REPRODUCTION_TEST.md`.<br>
**Limitation:** the public repository cannot supply the private final model file by itself.
