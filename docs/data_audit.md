# Data Audit - GOV-01 Road Damage Image Classifier

**Audit date:** 2026-07-28  
**Audited data path:** `data/raw/Dataset`  
**Implementation:** `src/audit_dataset.py`  
**Evidence:** `docs/image_manifest.csv` and the local ignored JSON report at `reports/dataset_audit.json`.

## Objective

Classify one road image as `Normal` or `Pothole` to support municipal report triage. This is decision support only, not a road-safety assessment.

## Audit conclusions

| Area | Finding | Risk | Decision / status |
|---|---|---|---|
| Source and access | Kaggle source and download method are documented in `data/README.md`. | Reproducibility risk if the source changes. | Record source URL and recheck licence when downloading. |
| Image integrity | All 1,401 images opened successfully. All are 64 x 64 JPEGs. | None found for corrupt files. | Accepted. |
| Class balance | Train: 293 Normal, 864 Pothole. Validation: 46 Normal, 62 Pothole. | Accuracy could hide weak Normal-class performance. | Use macro F1 plus class-level precision and recall. |
| Split structure | Test contains 136 flat image files rather than class folders. Every test image is an exact duplicate of training and/or validation data. | The supplied test folder is not an independent evaluation set. | Blocker: do not use this test folder for final evaluation. |
| Exact duplicates | 140 duplicate hash groups cross the supplied splits: 75 train-test, 58 validation-test, 3 across all three splits, and 4 train-validation. | Leakage can make validation and test results look better than they are. | Blocker: rebuild a clean split from unique images before training. |
| Groups / repeated scenes | No subject, scene, video, location, or source-group metadata is available. | Near-duplicate or same-scene leakage may remain. | Limitation: document this and inspect any available source metadata. |

## Split and leakage decision

The provided split is **not model-ready**. The project will not train or tune a model until a clean split is rebuilt from unique images. The supplied test folder will not be used because all 136 test files overlap with training and/or validation data.

The clean labeled pool contains 1,228 unique image hashes: 337 `Normal` and 891 `Pothole`. The planned scheme is a fixed-seed, stratified 70%/15%/15% train/validation/test split. A clean split must keep every exact duplicate in one split only. If source or scene-group metadata becomes available, it must also stay within one split. The actual resulting counts and zero-overlap check will be written to `docs/split_summary.csv` after the split is created.

## Preprocessing boundary

Images will be resized and normalized consistently. Random augmentation, if used, will be applied to training images only. Validation and test images will be transformed without random augmentation. The final preprocessing implementation must be named in the Colab notebook before model training begins.

## Gate status

**RED — repair required before modeling.**

### Required next actions

1. Build a clean split from unique labeled images; do not use the supplied flat test folder.
2. Record the resulting clean split counts and zero-overlap check.
3. Update this document and `PROJECT_STATUS.md`, then commit the verified Data Gate evidence.
