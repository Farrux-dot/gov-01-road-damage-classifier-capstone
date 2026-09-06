# V2 V1 Integration-Readiness Audit

## Purpose

This audit asks one question: **can part of the completed V1 image dataset later supplement V2 without weakening V1 evidence or creating obvious data leakage?**

It does not merge images, alter V1, create a V2 split, or train a model.

## Conservative eligibility rule

Only V1's clean `train` folder is considered for later V2 review. V1's existing `validation` and protected `test` folders stay reserved. They are not candidates for V2 integration.

This preserves the evidence behind the completed V1 model and avoids casually reusing its evaluation images.

## Label compatibility

| V1 binary label | V2 status | Reason |
| --- | --- | --- |
| `Pothole` | Maps to `pothole` | The class meaning matches the planned V2 pothole condition. |
| `Normal` | Needs visual review before any `normal_asphalt` use | A binary non-pothole label does not prove that an image has no shadow, puddle, stain, marking, repair, or unpaved surface. |

V1 has no object boxes. It may later support V2 image-level multi-class or multi-label work after review, but it cannot supply V2 object-detection annotations unless boxes are manually created.

## Audit checks

The reusable implementation is `src/audit_v1_v2_integration.py`. It checks:

1. V1 training image readability, observed labels, resolution, and exact duplicates.
2. Exact SHA-256 duplicate content between eligible V1 training images and all SVRDD source splits.
3. Counts of the V1 validation and protected-test images that remain reserved.

Run from the repository root:

```text
python -B src/audit_v1_v2_integration.py \
  --v1-clean-split data/processed/clean_split \
  --svrdd-extracted-dir data/raw/v2/svrdd/extracted \
  --output reports/v2_v1_integration_audit.json
```

The JSON report is ignored by Git because it is locally generated evidence.

## Results

Audit run date: 2026-09-06.

| Check | Result |
| --- | --- |
| Eligible V1 training images audited | 860 |
| Eligible `Pothole` images | 624 |
| Eligible `Normal` images | 236 |
| Image resolution | 64 x 64 for all 860 images |
| Unreadable eligible images | 0 |
| Exact duplicate groups within eligible V1 training data | 0 |
| Exact duplicate groups between eligible V1 training data and SVRDD | 0 |
| V1 validation images kept reserved | 185 (51 Normal, 134 Pothole) |
| V1 protected-test images kept reserved | 183 (50 Normal, 133 Pothole) |

## Result interpretation

The 624 V1 `Pothole` training images are structurally compatible with future **image-level** V2 pothole work. They have only binary image labels and no boxes, so they are not usable for V2 object detection without new manual box annotations.

The 236 V1 `Normal` training images are **not yet accepted as `normal_asphalt`**. Their binary source label says only that they are not labelled as potholes; it does not prove that they contain no shadows, puddles, stains, markings, repairs, or unpaved road. A separate visual review is required before any mapping decision.

The zero exact-duplicate result is useful, but it does not detect visually similar images, the same road scene at a different moment, or source-group leakage. A future combined-source audit must still check these risks before any V2 split is built.

## Current integration decision

**Needs V1 Normal visual review.** No V1 image has been copied or merged into V2. The next small task is a stratified visual review of the V1 `Normal` training images, focused on whether they are truly clear asphalt or contain V2 look-alikes.
