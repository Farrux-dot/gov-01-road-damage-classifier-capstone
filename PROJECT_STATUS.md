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
- Ran frozen MobileNetV2 transfer learning and selected it as the validation candidate with Macro F1 `0.915463`.

## Current task

Evaluate the frozen MobileNetV2 candidate once on the clean protected test split, then save and reload its complete inference artifact.

## Next

- Keep the Colab preprocessing evidence with the project records.
- Evaluate the already locked MobileNetV2 candidate on the clean test split once only.
- Save the model, image-processing rules, class mapping, and a reload-proof prediction.

## Known problems / blockers

- The supplied test folder remains excluded because it contains duplicate images, but the derived clean split has zero exact-hash overlap.
- The selected MobileNetV2 candidate has not been evaluated on the clean test split or saved as a reloadable inference artifact yet.
