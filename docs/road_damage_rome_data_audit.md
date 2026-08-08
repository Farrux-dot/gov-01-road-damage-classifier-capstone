# Version 2 Data Audit — Road Damage Dataset

**Audit date:** 2026-08-08

## Source and scope

- **Kaggle access page:** [Road Damage Dataset: Potholes, Cracks and Manholes](https://www.kaggle.com/datasets/lorenzoarcioni/road-damage-dataset-potholes-cracks-and-manholes).
- **Authoritative citation:** [Zenodo DOI 10.5281/zenodo.17834373](https://doi.org/10.5281/zenodo.17834373).
- **Local raw-data path:** `data/raw/road_damage_rome/data/` (ignored by Git).
- **Downloaded archive:** `data/raw/archive (4).zip`, 185.17 MB.
- **Licence note:** the dataset publication states CC BY 4.0, while the Kaggle page shows MIT. For this project, retain source attribution and document the publication's CC BY 4.0 statement; do not redistribute the raw data through Git.

The Version 2 model remains a binary **pothole-presence** classifier:

- `Pothole`: an image has at least one source annotation with category `pothole`.
- `No_pothole`: an image has no pothole annotation. It can contain cracks and/or manholes, so it does **not** mean a perfectly undamaged road.

The project does not assess pothole size, severity, danger, or repair priority.

## Integrity and annotation results

| Check | Result | Decision |
|---|---:|---|
| COCO image records | 2,009 | Accepted |
| JPEG files found | 2,009 | Accepted; every record has its image file |
| Total source annotations | 4,737 | Accepted |
| Image readability | 2,009 / 2,009 readable | Accepted |
| Image dimensions | 2,009 / 2,009 are 640 x 360 | Accepted |
| Missing image records | 0 | Accepted |
| Unlisted JPEG files | 0 | Accepted |
| Annotation references to unknown images | 0 | Accepted |
| Exact duplicate hash groups | 5 | Remove duplicate copies before splitting |
| Non-positive bounding boxes | 1 crack annotation with zero height | Does not change the image-level `No_pothole` label; retain raw data and record the limitation |
| Boxes extending outside the image | 45 | Bounding-box issue only; image-level binary labels remain usable |

The source categories and their object counts are: 1,261 potholes, 2,519 cracks, and 957 manholes.

## Binary image-label distribution

| Binary label | Images before duplicate removal | Images after keeping one file from each exact duplicate group |
|---|---:|---:|
| Pothole | 795 | 792 |
| No_pothole | 1,214 | 1,212 |
| Total | 2,009 | 2,004 |

Every duplicate group has a consistent binary label. The five duplicate copies must not appear in more than one derived split.

## Split and leakage risk

The provider supplies no train, validation, or protected-test split. Filenames provide only six conservative capture-date groups: `20250216`, `20250218`, `20250219`, `20250223`, `20250226`, and `unknown_capture_group`.

The unknown group contains 348 images whose filenames do not contain a capture date. There is no explicit video identifier. Therefore, a fully verified video-level split is not possible from the supplied metadata.

**Decision:** do not use a random image-level split. The next implementation must remove exact duplicate copies and create a reproducible, approximate 70%/15%/15% split that keeps each inferred capture-date group in only one split. This reduces likely frame leakage but remains a documented limitation.

## Derived clean split (created 2026-08-08)

`src/build_road_damage_rome_split.py` retained one canonical file from each exact duplicate group and copied the resulting 2,004 unique images to the ignored folder `data/processed/road_damage_rome_clean_split/`.

| Derived split | Capture groups kept together | Total | No_pothole | Pothole | Share of clean pool |
|---|---|---:|---:|---:|---:|
| Train | 20250218, 20250219 | 1,398 | 821 | 577 | 69.76% |
| Validation | unknown_capture_group | 348 | 240 | 108 | 17.37% |
| Protected test | 20250216, 20250223, 20250226 | 258 | 151 | 107 | 12.87% |

The fixed group assignment is intentionally approximate rather than an exact 70%/15%/15% split. Exact-hash verification found **zero overlap** between every pair of derived splits. The protected test split is now locked: it must not be loaded for model selection, threshold choice, or retraining.

## Shadow and repaired-road requirement

This dataset gives useful non-pothole examples of cracks and manholes. However, it has no dedicated label for shadows, fresh repairs, road markings, drainage covers, or clean pavement. We must not claim that the model can distinguish these cases until they are tested.

After the clean split is created, we will make a separately documented, labeled external challenge set for those confusing cases. It will not replace or contaminate the protected test split.

## Gate status

**YELLOW — the data is ready for an exploratory Version 2 training workflow, with the documented capture-group and challenge-set limitations.**

**Preprocessing implementation prepared:** `notebooks/GOV_01_v2_preprocessing.ipynb` loads the train and validation folders at 224 x 224 RGB, applies small random transformations to training images only, and deliberately leaves the protected test images unloaded. Its exact configuration is recorded in `docs/road_damage_rome_preprocessing_manifest.json`.

Required next action: execute that preprocessing notebook and record its real folder and batch-shape output. No Version 2 model has been trained or evaluated.

## Reproducible evidence

- `src/audit_road_damage_coco.py` is the audit implementation.
- `docs/road_damage_rome_image_manifest.csv` lists every image, its binary label, source classes, group, and SHA-256 hash.
- `docs/road_damage_rome_clean_image_manifest.csv` records every retained canonical image and its derived split.
- `docs/road_damage_rome_split_summary.csv` records the derived split counts and group allocation.
- `src/build_road_damage_rome_split.py` is the reproducible clean-split implementation.
- `reports/road_damage_rome_audit.json` is the local generated audit report and remains ignored by Git.
