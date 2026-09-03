# V2 SVRDD Visual Review

## Purpose

This is a **manual label-sanity check** before V2 label conversion. The contact sheets show a small, reproducible sample of images from the supplied SVRDD **training** split. They do not measure model quality and they do not use the supplied validation or test images to make any modeling decision.

The focus class is drawn in red. Other source boxes in the same image are drawn in yellow.

## Create the review sheets

Run this from the repository root after the raw SVRDD files have been extracted:

```text
python -B src/review_svrdd_samples.py \
  --images-dir data/raw/v2/svrdd/extracted/train \
  --metadata data/raw/v2/svrdd/metadata/train.metadata.jsonl \
  --output-dir data/raw/v2/svrdd/visual_review \
  --samples-per-class 8 \
  --seed 42
```

The output folder is under `data/raw/`, so it is ignored by Git. It contains seven contact sheets and `review_manifest.json`, which records exactly which images were selected.

## Review checklist

For every source class, inspect the eight selected images and record your findings before converting labels:

| Source class | Check manually | Review result |
| --- | --- | --- |
| Longitudinal crack | Is the red box on a road crack rather than a shadow or marking? | Pending |
| Transverse crack | Is the red box on a road crack rather than a shadow or marking? | Pending |
| Alligator crack | Is the red box on a clustered crack pattern? | Pending |
| Pothole | Is the red box on a physical hole/depression, not a shadow, puddle, stain, or manhole? | Pending |
| Manhole cover | Is the red box on a cover rather than a pothole? | Pending |
| Longitudinal patch | Is the red box on a repair/patch aligned with the road direction? | Pending |
| Transverse patch | Is the red box on a repair/patch across the road direction? | Pending |

## What to write after you inspect the sheets

For each row, replace `Pending` with one of these honest outcomes:

- **Accept for conversion:** the sampled labels match the source class well enough for the stated V2 mapping.
- **Needs exclusion rule:** a recurring confusing case requires a written mapping or exclusion rule.
- **Source concern:** labels are too inconsistent; do not use that class until a larger review is completed.

Record the number of questionable images and their filenames from `review_manifest.json`. Do not change source labels in place.

## Limits

- Eight images per class is a small sanity check, not a statistical estimate of full-dataset label quality.
- SVRDD has no dedicated labels for shadows, puddles, stains, clean asphalt, or unpaved road. A separate look-alike source is still required for those planned V2 labels.
- This review uses only the source training split to avoid using source validation/test data to guide later modeling decisions.
