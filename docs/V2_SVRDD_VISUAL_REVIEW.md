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
| Longitudinal crack | Is the red box on a road crack rather than a shadow or marking? | Accept for conversion — reviewed 8 training examples; source class matched the visible pattern. |
| Transverse crack | Is the red box on a road crack rather than a shadow or marking? | Accept for conversion — reviewed 8 training examples; source class matched the visible pattern. |
| Alligator crack | Is the red box on a clustered crack pattern? | Accept for conversion — reviewed 8 training examples; source class matched the visible pattern. |
| Pothole | Is the red box on a physical hole/depression, not a shadow, puddle, stain, or manhole? | Accept for conversion — reviewed 8 training examples; source class matched the visible pattern. |
| Manhole cover | Is the red box on a cover rather than a pothole? | Accept for conversion — reviewed 8 training examples; source class matched the visible pattern. |
| Longitudinal patch | Is the red box on a repair/patch aligned with the road direction? | Accept for conversion — reviewed 8 training examples; source class matched the visible pattern. |
| Transverse patch | Is the red box on a repair/patch across the road direction? | Accept for conversion — reviewed 8 training examples; source class matched the visible pattern. |

## Recorded review outcome

- Review date: 2026-09-03
- Reviewer conclusion: all 56 displayed training examples were recognizable and matched their supplied source classes.
- Limitation: the image quality and small preview size made some details difficult to see. This is a small manual sanity check only; it does not certify semantic accuracy for every image or box in the complete 8,000-image source.
- No questionable filename was recorded during this review.

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
