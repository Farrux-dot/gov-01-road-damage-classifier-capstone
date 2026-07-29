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

The provided split was **not model-ready**, so the supplied flat test folder was excluded. A clean split was rebuilt from 1,228 unique image hashes: 337 `Normal` and 891 `Pothole`.

The derived split uses fixed-seed (`42`), stratified 70%/15%/15% splitting. `src/build_clean_split.py` copies only unique labeled images into `data/processed/clean_split/` and then verifies zero exact-hash overlap across splits.

| Derived split | Total | Normal | Pothole |
|---|---:|---:|---:|
| Train | 860 | 236 | 624 |
| Validation | 185 | 51 | 134 |
| Test | 183 | 50 | 133 |

The zero-overlap verification passed. The reproducible evidence is in `docs/split_summary.csv` and `docs/clean_image_manifest.csv`; the raw and derived image folders remain excluded from Git.

## Preprocessing boundary

The named implementation is `notebooks/GOV_01_data_preprocessing.ipynb`, with configuration recorded in `docs/preprocessing_manifest.json`. Images are resized to 224 x 224 RGB. Random flip, rotation, and zoom are applied only to training images. Validation and test images receive no random augmentation.

Pixel scaling is model-specific: the baseline CNN will use `Rescaling(1/255)` inside the model, while MobileNetV2 will use its own `preprocess_input` inside the transfer-learning model. Neither approach fits learned preprocessing statistics from validation or test images.

## Gate status

**YELLOW — clean split and preprocessing implementation are prepared; execute and verify the notebook in Colab before model comparison expands.**

### Required next actions

1. Run the preprocessing notebook against the clean split in Colab and verify the loaders.
2. Confirm that random augmentation runs only in the training loader.
3. Update this document and `PROJECT_STATUS.md`, then commit the verified Data Gate evidence.
