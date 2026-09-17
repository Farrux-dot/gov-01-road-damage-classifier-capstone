# V2 Class Coverage Report

**Updated:** 2026-09-17
**Status:** pre-split candidate evidence only — not approved for V2 training

## What this report counts

The V2 sources use different types of labels. A full image, a positive
multi-label condition, and an object box are different units and must not be
added together. This report keeps them separate.

## Current accepted sources

| Source | Candidate images | What it contributes |
| --- | ---: | --- |
| SVRDD source training split | 6,000 | Pothole, crack, manhole-cover, and repaired-road boxes and source mappings |
| V1 clean training Pothole | 624 | Image-level pothole evidence only; no boxes |
| GitHub pothole-detection | 1,241 | Student-approved pothole images with YOLO boxes |
| StreetSurfaceVis | 1,721 | Normal-asphalt and unpaved-road image-level candidates |
| CeyMo | 2,097 | Road-marking-positive images and boxes |
| **Total** | **11,683** | Pre-split candidate pool |

## Provisional multi-class primary labels

| Primary label | Candidate images |
| --- | ---: |
| Pothole | 2,337 |
| Crack | 3,907 |
| Manhole cover | 1 |
| Repaired road | 1,620 |
| Normal asphalt | 791 |
| Unpaved road | 930 |
| Road marking | 0 |

The count of one for `manhole_cover` is not a claim that only one manhole is
available. The current one-label priority rule gives pothole, crack, or
repaired-road priority when multiple conditions appear in one image. This is a
blocker for honest multi-class training.

## Positive-image multi-label coverage

| Condition | Images marked positive |
| --- | ---: |
| Pothole | 2,337 |
| Crack | 4,253 |
| Manhole cover | 1,688 |
| Repaired road | 2,077 |
| Road marking | 2,097 |

StreetSurfaceVis supports the two surface-type labels but does not provide a
complete set of positive/negative labels for all V2 conditions.

## Detection box coverage

| Object label | Valid boxes |
| --- | ---: |
| Pothole | 4,740 |
| Crack | 7,335 |
| Manhole cover | 2,517 |
| Repaired road | 5,089 |
| Road marking | 3,484 |

The 624 V1 pothole images have no boxes, so they are not included in this
table. The GitHub pothole source contributes 4,061 of the pothole boxes.

## Conditions still missing as dedicated accepted sources

- Shadow
- Puddle
- Road stain

Do not turn a generic negative image into one of these labels automatically.
Each needs an explicit source or careful manual labels.

## Safety checks completed for this inventory

- 1,241 GitHub pothole records were included only when the audit decision was
  `keep`.
- Two exact duplicate image copies and one invalid zero-width source box line
  were excluded before integration.
- V1 validation and protected-test images are excluded.
- SVRDD validation and test source packages are excluded.
- No exact SHA-256 duplicate group remains within the 11,683 candidate rows.
- The inventory records repository-relative paths only; no local drive paths
  are published.

## Decision

The data pool is larger and pothole detection coverage is stronger, but V2 is
still not ready to train. The next data task is to create leakage-safe splits
and task-specific inclusion rules after resolving the multi-class manhole
collapse and the missing look-alike labels.
