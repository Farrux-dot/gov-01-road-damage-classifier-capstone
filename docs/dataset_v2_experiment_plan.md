# Version 2 Data and Model Experiment Plan

## Purpose

Version 1 (`mobilenetv2_frozen_v4`) remains the project's final, reported model for the original 64 x 64 Kaggle dataset. It must not be modified or re-evaluated as part of this experiment.

The purpose of this separate experiment branch is to investigate whether a higher-resolution, more varied real-road dataset can reduce false positives on visually confusing road scenes, such as shadows and asphalt repairs. The observed tree-shadow prediction is a qualitative stress case only; it is **not** part of the Version 1 protected-test result.

## Proposed Version 2 source

- **Candidate dataset:** HRP4K: A high-resolution perspective-view road image dataset for pothole detection.
- **Official record:** [Zenodo DOI 10.5281/zenodo.17522874](https://doi.org/10.5281/zenodo.17522874).
- **Publication:** [Scientific Data dataset description](https://doi.org/10.1038/s41597-026-07317-w).
- **Licence:** CC BY 4.0; retain the required attribution in the final documentation.
- **Reported contents:** 6,003 high-resolution road images: 4,003 images with at least one annotated pothole and 2,000 pothole-absent road images. Labels are supplied in YOLO and COCO formats.
- **Reported provider split:** 4,203 train, 900 validation, and 900 protected-test images, constructed by video group to reduce frame leakage.

This source is a good candidate because it contains real, high-resolution images and explicitly includes pothole-absent road scenes. It is still limited to vehicle-mounted, forward-facing imagery from Zhejiang Province, China. It is not evidence that the final model will work in every city, weather condition, or camera angle.

## Task definition

The GOV-01 scope stays binary image classification:

- `Pothole`: an image has at least one valid pothole annotation.
- `Normal`: an image is in the provider's pothole-absent negative set.

This experiment does **not** change the project into pothole severity assessment, repair prioritisation, or safety assessment. It also does not claim object-location detection in the Streamlit app.

## Data Gate required before training

1. Confirm that Disk D has sufficient free space before downloading the high-resolution archive. Download and extract only to a local ignored folder such as `data/raw/hrp4k/`.
2. Record the exact source URL, download date, archive size, licence, attribution text, and any access requirements in `data/README.md`.
3. Audit every image and annotation pair: readable files, resolution distribution, class counts, missing labels, corrupt files, exact duplicates, and provider-split overlap.
4. Check that the file-name video groups do not cross the provider's train, validation, and test boundaries.
5. Create a new Version 2 manifest and split summary. Keep raw images, derived images, downloaded archives, and model files out of Git.
6. Review the audit findings before any model is trained.

## Modeling and evaluation rule

- Train only on the Version 2 training split.
- Select one candidate using Version 2 validation macro F1, plus class-level precision and recall.
- Do not open or tune against the Version 2 protected test split until the candidate is locked.
- Compare Version 2 and Version 1 only with clear labels: they use different datasets, so their scores are not a direct like-for-like benchmark.
- Keep difficult real images (shadows, repairs, wet roads, drains, and cracks) as a documented external challenge set. It is useful for qualitative robustness checks but must not be reported as a protected-test metric unless it is fully sourced and labeled before model selection.

## Current status

> **Current update (2026-08-07): BLOCKED AT DATA AUDIT.** The local HRP4K archive has been inspected. Its `train.json` lists 4,203 images while the archive contains only 2,286 train JPEG files. See `docs/hrp4k_data_audit.md`. No Version 2 model has been trained or evaluated.

## Replacement source selected (2026-08-08)

HRP4K will not be used because its current official archive is incomplete. The replacement candidate is the Road Damage Dataset: Potholes, Cracks and Manholes. Its actual audit evidence is in `docs/road_damage_rome_data_audit.md`.

The Version 2 task is now `Pothole` versus `No_pothole`, where `No_pothole` means that the image has no pothole annotation. Cracks and manholes are intentionally retained as difficult non-pothole examples. The source has passed initial file-integrity checks but has not yet passed the full Data Gate because a duplicate-free, group-aware split still must be created and verified.

**PLANNED — no HRP4K files have been downloaded, audited, used for training, or used to claim a performance result.**
