# Data Audit - GOV-01 Road Damage Image Classifier

**Audit date:** 2026-07-27  
**Audited data path:** `data/raw/Dataset`  
**Audit method:** `src/audit_dataset.py` plus a read-only image-format and dimension check.

## Dataset structure

| Split | Normal | Pothole | Total | Status |
|---|---:|---:|---:|---|
| Train | 293 | 864 | 1,157 | Class folders present |
| Validation | 46 | 62 | 108 | Class folders present |
| Test | Not supplied as folders | Not supplied as folders | 136 | Flat image files; labels require clarification |

The test filenames start with `normal` (71 files) or `pothole` (65 files), but filenames are not automatically treated as verified labels. The dataset documentation or source structure must confirm whether those prefixes are the intended ground-truth labels before the test set is used for final evaluation.

## Image quality and format

- All **1,401** image files opened successfully; no corrupt or unreadable images were found.
- All images are **JPEG** files.
- All images are **64 x 64 pixels**.

## Class balance

The training data is imbalanced: 864 of 1,157 images (about **74.7%**) are potholes, while 293 (about **25.3%**) are normal roads. Accuracy alone may therefore be misleading. The project will use macro F1 as the primary metric and will report per-class precision and recall.

## Duplicate and leakage check

Seven exact duplicate images were found between the training and validation splits. This is leakage because a model can see the same image during training and validation. These duplicates must be removed from one split or the affected split must be rebuilt before model training and model selection.

No conclusion is made yet about test-set leakage because the test labels and test-split design need clarification first.

## Decisions before modeling

1. Resolve the seven train/validation duplicates without changing the raw dataset archive.
2. Confirm the intended labels for the 136 flat test images.
3. Document the resulting clean split strategy before training.
4. Do not train or report model metrics until these items are resolved.
