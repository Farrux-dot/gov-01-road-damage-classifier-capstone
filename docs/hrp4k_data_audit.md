# HRP4K Version 2 Data Audit

**Audit date:** 2026-08-07
**Audited local path:** `data/raw/hrp4k/HRP4K/HRP4K` (ignored by Git)
**Source archive:** `HRP4K.zip`, downloaded from the [official Zenodo record](https://doi.org/10.5281/zenodo.17522874)
**Observed archive size:** 8.06 GB
**Licence reported by the source:** CC BY 4.0

## Scope

This is the Version 2 experiment dataset for binary image classification only:

- `Pothole`: an image with at least one valid pothole annotation.
- `Normal`: an image with no pothole annotation.

It does not change the GOV-01 project into severity assessment, repair prioritisation, or object detection.

## Initial file and annotation check

The archive is readable and contains 10,102 entries. It contains official COCO-format files named `train.json`, `valid.json`, and `test.json`. Their one category is `pothole` with `category_id` 0.

| Provider split | Image records in JSON | Pothole annotations in JSON | JPG files present after extraction | Result |
|---|---:|---:|---:|---|
| Train | 4,203 | 5,259 | 2,286 | **Blocked: 1,917 listed images are missing** |
| Validation | 900 | 1,037 | 900 | File count matches JSON |
| Test | 900 | 921 | 900 | File count matches JSON |

The first train image record reports a 3,840 x 2,160 image, confirming that this source is much higher resolution than Version 1's 64 x 64 images. This is only a metadata observation; the full resolution distribution has not yet been audited.

## Blocking finding

The training JSON lists 4,203 images, but the downloaded archive itself contains only 2,286 JPEG files under `train/images`. The 1,917 missing files were also checked inside `HRP4K.zip`, so this is **not an incomplete local extraction**.

Because the annotations and available training images do not match, the Version 2 dataset is **not model-ready**. Training, rebuilding splits, computing class balance, duplicate hashing, and any test evaluation are paused.

## Required resolution

1. Check the official Zenodo record and associated documentation for a corrected or supplementary training-image archive.
2. If the provider supplies corrected files, download them to the ignored `data/raw/hrp4k/` folder and repeat this file/annotation check.
3. Only after every annotation image has a corresponding readable file may we complete the remaining audit: image integrity, resolution distribution, class balance, exact duplicate hashes, provider-split overlap, and group/leakage checks.

## Decision

**RED — do not train a Version 2 model from the current HRP4K archive.**

Version 1 (`mobilenetv2_frozen_v4`) remains the project's reported final model and its protected-test result is unchanged.
