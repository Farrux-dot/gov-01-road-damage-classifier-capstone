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

## Current task

Implement the class-weighted CNN experiment using the same training and validation split.

## Next

- Keep the Colab preprocessing evidence with the project records.
- Compare the unweighted and class-weighted CNN using validation Macro F1 and Normal recall.
- Compare later approaches on validation data; use the clean test split once for the final selected model.

## Known problems / blockers

- The supplied test folder remains excluded because it contains duplicate images, but the derived clean split has zero exact-hash overlap.
- The unweighted CNN is weak at identifying Normal images (validation recall `0.352941`), so it is not a final candidate.
