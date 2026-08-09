# Project Status

## Project

GOV-01 Road Damage Image Classifier

## Current stage

Demo Deployment (Module 8 Class 5) — Yellow

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
- Added the local Streamlit demo structure: interface, reusable inference module, smoke test, and local deployment instructions.

## Current task

Run the local Streamlit demo with the private saved `.keras` model and one known-good image.

## Next

- Copy the privately saved `mobilenetv2_frozen_v4.keras` file into the local `artifacts/` folder; it stays ignored by Git.
- Install requirements, run `python smoke_test.py --image <path>`, and then run `streamlit run app.py`.
- Record one known-good local prediction and a screenshot of the working app.
- Preserve the final test result; do not tune or retrain V4 after test access.

## Known problems / blockers

- The supplied test folder remains excluded because it contains duplicate images, but the derived clean split has zero exact-hash overlap.
- MobileNetV2 v3 applied random augmentation during validation inference. Its historical metrics are invalid and must not be used for selection or comparison.
- The `.keras` model file is intentionally not stored in GitHub, so the first deployment route is local Streamlit with Colab as fallback.

## Version 2 experiment branch

- Branch: `experiment_dataset_v2_finetuning`.
- Goal: prepare and audit a higher-resolution, more varied dataset before training a new experimental model.
- Status: blocked at the initial data audit. The inspected HRP4K archive has 1,917 training-image records in `train.json` without matching image files. See `docs/hrp4k_data_audit.md` and issue `DQ-04`.
- Replacement source: the Rome Road Damage Dataset has passed the V2 audit and now has a duplicate-free, capture-group-aware derived split with zero exact-hash overlap. Evidence is in `docs/road_damage_rome_data_audit.md`, `docs/road_damage_rome_clean_image_manifest.csv`, and `docs/road_damage_rome_split_summary.csv`.
- Version 2 preprocessing is prepared in `notebooks/GOV_01_v2_preprocessing.ipynb`. It loads only train and validation images, with random augmentation restricted to training. The protected V2 test folder remains unloaded until a model candidate is locked.
- The V2 preprocessing notebook was executed in Google Colab and verified a real `(32, 224, 224, 3)` training batch with matching binary labels. This is data-loader evidence only; no V2 model result exists yet.
- V2 naive and unweighted-CNN validation references were run. The CNN had Macro F1 `0.408163` and pothole recall `0.0`, exactly matching the naive majority rule; it is rejected.
- V2 class-weighted CNN improved validation Macro F1 to `0.479609` and pothole recall to `0.231481`, but it still missed 83 of 108 potholes. It is not a candidate. The next controlled V2 experiment is frozen MobileNetV2 transfer learning with the recorded class weights.
- V2 frozen MobileNetV2 improved validation Macro F1 to `0.538563` and pothole recall to `0.518519`, but produced 99 false pothole alerts. It is the current V2 validation leader, not yet a candidate. The next controlled experiment is cautious final-layer fine-tuning; V2 protected test remains unused.
- V2 fine-tuned MobileNetV2 is the current validation leader: Macro F1 `0.539904`, pothole recall `0.583333`, and 109 false pothole alerts. The improvement over frozen MobileNetV2 is small. Threshold selection will use validation Macro F1 only before any V2 protected-test access.
- Guardrail: Version 1 V4 metrics and its protected test remain final and must not be changed.
