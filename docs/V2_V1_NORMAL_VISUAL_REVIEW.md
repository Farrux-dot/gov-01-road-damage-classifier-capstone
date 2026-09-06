# V1 Normal Training-Image Visual Review

## Purpose

V1's `Normal` class means only **not labelled as a pothole**. It is not proof
that an image shows clear normal asphalt. This review is required before any
V1 Normal image could later be considered as a V2 `normal_asphalt` example.

This step does not change V1 labels, copy images, merge datasets, create a V2
split, or train a model.

## Review aid

Run this from the repository root after the V1 clean split is available:

```text
python -B src/review_v1_normal_samples.py \
  --normal-dir data/processed/clean_split/train/Normal \
  --output-dir reports/v2_v1_normal_review \
  --sample-count 24 \
  --sheet-size 8 \
  --seed 42
```

The output is intentionally ignored by Git. It contains three contact sheets
and `review_manifest.json`, which records exactly which files were sampled.

The source images are 64 x 64 pixels. The review sheet enlarges them with
nearest-neighbour pixels so it does not invent visual detail; therefore their
low original resolution remains visible.

## How to review each image

For every image, choose one manual decision:

| Decision | Meaning |
| --- | --- |
| `clear_normal_asphalt` | Road surface is sufficiently clear for a possible future normal-asphalt example. |
| `shadow_or_lighting` | Shadow, glare, or lighting pattern is the main road feature. |
| `puddle_or_reflection` | Water or reflection could confuse a future model. |
| `road_stain_or_marking` | Stain, paint, lane marking, or similar non-damage pattern is visible. |
| `repair_or_patch` | Repaired road or patch is visible. |
| `unpaved_or_other` | Unpaved surface or another non-target condition is present. |
| `uncertain` | The 64 x 64 source image is too unclear for an honest decision. |

Do not call an image `clear_normal_asphalt` merely because no pothole is seen.
Keep `uncertain` images out of any future V2 normal-asphalt data.

## Review outcome

Review date: 2026-09-06.

The selected V1 Normal images were rejected for V2 use. Their original 64 x
64 resolution is too low to make defensible manual distinctions between clear
asphalt and look-alikes such as shadows, lane markings, repairs, or other road
surface patterns. Relabelling them as `normal_asphalt` would create unreliable
training evidence.

No V1 Normal image is approved for a V2 label, copied into V2, or used for
training. The generated contact sheets are only local review evidence and stay
ignored by Git.
