# Project Status

## Project

GOV-01 Road Damage Image Classifier

## Current stage

Model Gate (Module 8) — Yellow

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

## Current task

Prepare the frozen MobileNetV2 transfer-learning comparison using the same validation split and class weights.

## Next

- Keep the Colab preprocessing evidence with the project records.
- Compare the class-weighted CNN and frozen MobileNetV2 using validation Macro F1, class-level recall, and error patterns.
- Use the clean test split once only after a final candidate is selected.

## Known problems / blockers

- The supplied test folder remains excluded because it contains duplicate images, but the derived clean split has zero exact-hash overlap.
- The class-weighted CNN improves Normal recall but increases Pothole-to-Normal errors; this trade-off must be compared with transfer learning.
