# V2 Data Intake Layout

This file describes where the original V2 datasets will go **after** a source has been approved. It does not mean that V2 images have been downloaded yet.

## Keep raw data outside Git

Raw ZIP archives and original images belong under the ignored folder `data/raw/v2/`. Git ignores this folder, so large datasets and source files will not be uploaded to GitHub.

Suggested layout after approval:

```text
data/raw/v2/
  rdd2022/
  svRDD_yolo/
  manual_lookalike_supplement/
```

## Required record before adding a source

Before placing anything in that folder, update `docs/v2_source_manifest.csv` with the exact source page, owner, license, download date, annotation format, and intended use.

## Important V2 boundaries

- Do not alter the V1 raw data, clean split, protected test set, saved model, or deployed app.
- Do not add raw data, ZIP files, model artifacts, tokens, or secrets to Git.
- Do not create a V2 train/validation/test split until sources have passed the data audit and duplicate checks.
- Use `docs/V2_ROAD_CONDITION_LABELING_GUIDE.md` when converting source labels or manually labeling images.
