# Data documentation

## Source and access

The raw images come from the [Kaggle Pothole Detection Dataset](https://www.kaggle.com/datasets/abhinavkulshreshth/pothole-detection-dataset) by `abhinavkulshreshth`. Kaggle listed the dataset as CC0 when this project plan was created. Recheck the dataset page and licence before downloading or redistributing.

Download the ZIP from Kaggle, extract it to `data/raw/`, and keep the extracted files out of Git. The raw data is ignored because it is large and externally sourced.

### Download instructions

1. Open the Kaggle dataset link above and sign in if prompted.
2. Click **Download** to save the ZIP archive.
3. Extract the archive into `data/raw/` in this repository.
4. The downloaded archive should be available under `data/raw/Dataset/`.
5. Do not commit the ZIP archive or raw image folders to GitHub.

## What one sample represents

One sample is one 64 x 64 JPEG road image. The supervised target is whether the image is in the `Normal` or `Pothole` class.

The model detects pothole presence only. It does not assess danger, physical size, severity, road safety, repair cost, or repair priority.

## Dataset size and split scheme

- **Downloaded archive:** 1,401 images: 1,157 in the supplied training folder, 108 in validation, and 136 in a flat test folder.
- **Usable labeled pool after exact-hash deduplication:** 1,228 images: 337 `Normal` and 891 `Pothole`.
- **Planned clean split:** stratified 70% training, 15% validation, and 15% test from the 1,228 unique labeled images, using a fixed random seed.
- **Supplied test folder:** excluded from final evaluation because every one of its 136 images is an exact duplicate of a training and/or validation image.

## Current dataset limitations

- The training data is imbalanced toward pothole images.
- There are 140 exact-duplicate groups across the provided splits. All 136 test images are duplicates of training and/or validation images, so the provided test folder is not an independent evaluation set.
- Seven duplicate groups cross the provided training and validation splits.
- The dataset may not represent all road surfaces, lighting, weather, camera angles, or damage types found in real municipal reports.

## Evidence files

- `docs/data_audit.md` records the audit findings, risks, and decisions.
- `docs/image_manifest.csv` lists every readable image path, split, observed label source, and SHA-256 hash.
- `docs/clean_image_manifest.csv` records the final derived split and supports the zero-overlap check.
- `docs/split_summary.csv` records the final class counts and split ratios.
- `src/audit_dataset.py` is the reusable audit implementation.
- `src/build_clean_split.py` is the reproducible clean-split implementation.
