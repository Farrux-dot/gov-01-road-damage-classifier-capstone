# V2 Source-Traceable Candidate Inventory

**Inventory date:** 2026-09-13
**Stage:** candidate inventory before near-duplicate review, final labelling, and splitting
**Training status:** not approved

## Purpose

This inventory records every currently eligible V2 candidate image, where it
comes from, which tasks it may support, and what evidence allows it to remain
a candidate. It does not copy images, change source labels, create final
train/validation/test splits, or train a model.

The detailed inventory is `docs/v2_candidate_inventory.csv`. It contains safe
repository-relative source paths and SHA-256 file hashes so later data-cleaning
steps can trace and compare every candidate.

## Inclusion rules

### SVRDD

- Included 6,000 converted records from the source **training** package as
  pre-split candidates.
- Kept the 1,000 source validation records and 1,000 source test records out of
  the candidate inventory. They remain reserved to protect evaluation
  separation and must not be used for training or tuning.
- The audited conversion provides mapped object boxes, multi-label fields, and
  the documented provisional multi-class priority label.
- The 56-image training sanity review supported the class mapping, but it did
  not certify every source image.

### V1

- Included only the 624 Pothole images from the clean V1 **training** split.
- Included no V1 Normal images.
- Included no V1 validation or protected-test images.
- These 624 images have image-level pothole labels but no object boxes, so they
  cannot train object detection without new manual box annotations.

### PaveBench

- Included only 109 individually approved detection-review records: 55
  Alligator, 43 Crack, and 11 Patch records.
- Mapped approved Alligator and Crack records to V2 `crack`.
- Mapped approved Patch records to V2 `repaired_road`.
- Included no PaveBench pothole records and no unclear, wrong-label, or
  wrong-box records.

### StreetSurfaceVis

- Included only source records marked `official_train=True` whose width and
  height are both at least 224 pixels.
- Included 791 `normal_asphalt` candidates and 930 `unpaved_road` candidates.
- The deterministic 100-image review supported 40/40 sampled normal-asphalt
  records and 59/60 sampled unpaved-road records. The unclear record
  `SSV-055` was excluded.
- Excluded all 265 records marked `official_train=False`, including the 17
  protected records below 1,024 pixels. Resolution never overrides split
  protection.
- These records support multi-class classification only. They do not provide
  complete nine-output multi-label truth or object boxes.

## Candidate counts by source

| Source | Candidate image records | Current meaning |
| --- | ---: | --- |
| SVRDD source training split | 6,000 | Mapped pre-split source candidates with boxes |
| V1 clean training Pothole | 624 | Image-level pothole candidates without boxes |
| PaveBench individually approved detection records | 109 | Human-reviewed candidates with boxes |
| StreetSurfaceVis source-training candidates | 1,721 | Sample-supported normal-asphalt and unpaved-road candidates without boxes |
| **Total** | **8,454** | Not a final training split |

## Task eligibility

| Possible task support | Images | Meaning |
| --- | ---: | --- |
| Multi-class, multi-label, and object detection | 6,109 | SVRDD and reviewed PaveBench records have boxes |
| Multi-class and multi-label only | 624 | V1 pothole records have no boxes |
| Multi-class only | 1,721 | StreetSurfaceVis has surface labels but no boxes or complete multi-label truth |

Task eligibility does not mean the data is ready for training. Remaining label,
near-duplicate, imbalance, and split checks still apply.

## Provisional multi-class primary labels

| Primary label | Candidate images |
| --- | ---: |
| `crack` | 4,005 |
| `repaired_road` | 1,631 |
| `pothole` | 1,096 |
| `manhole_cover` | 1 |
| `normal_asphalt` | 791 |
| `unpaved_road` | 930 |

The `manhole_cover` count of one is a serious feasibility warning. It does not
mean SVRDD contains only one manhole. The provisional one-label priority rule
selects pothole, crack, or repaired road before manhole when several conditions
appear in one image. As a result, manholes are hidden from the primary-label
count.

**Decision:** do not build the V2 multi-class training split from these primary
labels yet. A later task must either create single-condition image crops from
the audited boxes or define another defensible method that gives
`manhole_cover` enough honest primary examples.

## Multi-label positive-image counts

One image may appear in more than one row of this summary:

| Positive condition | Images containing the condition |
| --- | ---: |
| `crack` | 4,351 |
| `repaired_road` | 2,088 |
| `manhole_cover` | 1,688 |
| `pothole` | 1,096 |

These counts show that multi-label classification represents mixed-condition
images more honestly than the current single-label priority rule.

## Detection object counts

| Box label | Objects |
| --- | ---: |
| `crack` | 7,433 |
| `repaired_road` | 5,100 |
| `manhole_cover` | 2,517 |
| `pothole` | 679 |

The 624 V1 pothole images are not included in the object count because they do
not have boxes.

## Exact-duplicate and separation checks

| Check | Result |
| --- | ---: |
| Candidate IDs | 8,454 unique |
| Candidate source paths | 8,454 existing files |
| Exact SHA-256 duplicate groups | 0 |
| Records in exact-duplicate groups | 0 |
| V1 validation or protected-test records included | 0 |
| SVRDD source validation or test records included | 0 |

The zero exact-duplicate result does not detect near duplicates, visually
similar road frames, or the same road segment photographed at a different
time. Those risks still require a later group/near-duplicate check before the
final split.

## Licence boundary

- SVRDD: CC BY 4.0 stated on the dataset card; recheck before redistribution.
- V1 Kaggle source: CC0 was listed when the project plan was created; recheck
  before redistribution.
- PaveBench: CC BY-NC-SA 4.0; this is non-commercial and share-alike.
- StreetSurfaceVis: CC-BY-SA is stated on the official Zenodo record; recheck
  before redistribution.

The inventory contains paths and evidence only. It does not redistribute the
raw images.

## Remaining blockers

1. Resolve the single-label `manhole_cover` collapse before multi-class model
   construction.
2. Add or human-label the remaining look-alike conditions: shadow, puddle,
   road stain, and road marking.
3. Check near duplicates and source groups, not only byte-identical files.
4. Decide task-specific inclusion rules because V1 potholes cannot support
   object detection without boxes.
5. Create new leakage-safe train, validation, and protected-test splits.
6. Recalculate class balance after all exclusions and splitting.
7. Complete the full V2 Data Gate before training any V2 model.

## Current decision

**The traceable candidate inventory is complete. It is pre-split evidence, not
a training dataset. V2 training remains blocked.**
