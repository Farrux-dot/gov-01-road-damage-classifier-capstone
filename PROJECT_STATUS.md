# Project Status

## Project

GOV-01 Road Damage Image Classifier

## Current stage

Model Gate (Module 8) — Green

## Completed

- Selected the GOV-01 Road Damage Image Classification scenario.
- Defined the initial scope: binary `Normal` vs. `Pothole` image classification for report triage.
- Created the project repository and initial code/documentation structure.
- Selected a public Kaggle dataset candidate and documented that data files will not be committed to Git.
- Completed an initial read-only dataset audit and recorded real findings in `docs/data_audit.md`.
- Rebuilt a clean duplicate-free stratified split from 1,228 unique labeled images and verified zero exact-hash overlap across train, validation, and test.
- Added the named image preprocessing notebook and manifest with training-only augmentation.
- Ran the preprocessing notebook in Google Colab; retain its output or a screenshot as supporting evidence.
- Added a documented modeling-readiness plan before model training.
- Added the first Model Gate notebook: a naive baseline and compact CNN baseline evaluated on validation data only.
- Added initial Model Gate evidence and artifact documentation; no model result has been claimed yet.
- Ran the naive and compact-CNN baselines in Colab and saved the real validation metrics and visual evidence.
- Ran the class-weighted CNN experiment and improved validation Macro F1 from `0.673898` to `0.775295`.
- Ran MobileNetV2 v3, then found that its validation images were incorrectly augmented; its results are documented but invalid for selection.
- Re-ran the corrected frozen MobileNetV2 v4 with random augmentation restricted to training images and recorded valid validation evidence.
- Locked `mobilenetv2_frozen_v4` as the candidate after it achieved validation Macro F1 `0.933126`.
- Evaluated the locked V4 candidate once on the protected clean test split, achieving Macro F1 `0.939901` and accuracy `0.950820`; no tuning followed test access.
- Saved the final model artifact in Colab and tracked its configuration and loading instructions.
- Reloaded the saved model in a fresh Colab runtime; it reproduced the known proof-image probability exactly (`0.907272`, difference `0.0`).

## Current task

Review the completed Model Gate evidence and prepare the next capstone deliverable.

## Next

- Keep the Colab preprocessing evidence with the project records.
- Preserve the final test result; do not tune or retrain V4 after test access.
- Keep the downloaded `.keras` model file safely outside Git.
- Use the documented final result and limitations when preparing the final capstone report or presentation.

## Known problems / blockers

- The supplied test folder remains excluded because it contains duplicate images, but the derived clean split has zero exact-hash overlap.
- MobileNetV2 v3 applied random augmentation during validation inference. Its historical metrics are invalid and must not be used for selection or comparison.
