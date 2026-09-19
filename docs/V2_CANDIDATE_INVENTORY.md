# V2 Source-Traceable Candidate Inventory

**Inventory date:** 2026-09-17
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

### GitHub pothole-detection

- Included 1,241 `keep` records from the student-approved GitHub pothole audit.
- The source supplies YOLO-format pothole boxes; the included records contain
  4,061 valid pothole boxes.
- Two byte-identical duplicate image copies and one invalid zero-width source
  box line were excluded by the audit before inventory integration.
- This is an unsplit source collection. It is a pre-split candidate source,
  not a validation or test set.

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

### Approved road-shadow subset from StreetSurfaceVis

- The student-approved initial review retained **66** road images where a shadow is
  visibly present. Seven are from the official non-training split and remain
  excluded to protect later evaluation.
- **59** of these images already exist in the inventory as `normal_asphalt`
  records. They are kept once and receive the additional multi-label tag
  `shadow`; no duplicate image record is created.
- A later 120-image review-only shortlist retained **96** additional
  source-training examples and excluded **24** no-shadow examples.
- Therefore **155** eligible training candidates receive the shadow tag.
- `shadow` is an extra multi-label condition, not a new primary multi-class
  road-condition output. It helps later work teach the model not to confuse a
  road shadow with pothole damage.
- These images have no object boxes. They support multi-label classification,
  not object detection.

### Clear no-shadow subset from StreetSurfaceVis

- A separate 60-image human review retained **51** `normal_asphalt` source-training
  images with no visible road shadow. The remaining **9** had a visible shadow,
  so they are excluded from this no-shadow subset.
- The 51 retained images are recorded in `docs/v2_no_shadow_manifest.csv` as a
  reviewed absence condition, `no_visible_road_shadow`. They do not add a new
  primary class or create duplicate inventory records.

### CeyMo

- Audited all 2,099 official source-training images and their XML annotations.
- Recorded every source image in `docs/v2_ceymo_candidate_manifest.csv`.
- Accepted 2,097 exact-unique images and excluded two redundant copies before
  integration. The duplicate with more annotated objects was kept; equal
  annotations used the alphabetically first source ID as a stable tiebreak.
- Retained 3,484 road-marking boxes after duplicate removal.
- These records support road-marking-positive multi-label evidence and object
  detection. They do not receive an automatic multi-class primary label
  because other V2 conditions in each complete scene were not exhaustively
  reviewed.


### Mendeley manhole and speed-breaker dataset

- Student approved only the `Good_Manhole` and `Speed_Breaker` folders.
- Removed within-folder byte-identical duplicates without deleting the raw downloaded source: **663** `Good_Manhole` images and **150** `Speed_Breaker` images remain in the raw selection. Three byte-identical pairs have conflicting folder labels, so all six records are held out in `docs/v2_mendeley_cross_label_duplicate_holdout.csv`.
- Excluded `Broken_Manhole`, `Uncovered_Manhole`, and `Square_Manhole` at the student's decision.
- The source has folder-level image labels only. It supports multi-class classification and limited positive-label evidence for multi-label work, but **does not provide boxes** and must not be used for object detection.
- These are supporting look-alike classes: they help a classifier avoid confusing manhole covers or speed bumps with potholes. They are not the final road-condition outputs.

## Candidate counts by source

| Source | Candidate image records | Current meaning |
| --- | ---: | --- |
| SVRDD source training split | 6,000 | Mapped pre-split source candidates with boxes |
| V1 clean training Pothole | 624 | Image-level pothole candidates without boxes |
| GitHub pothole-detection | 1,241 | Student-approved pothole candidates with YOLO boxes |
| StreetSurfaceVis source-training candidates | 1,721 | Sample-supported normal-asphalt and unpaved-road candidates without boxes; 155 approved road-shadow examples and a separate 51-image clear no-shadow review subset |
| CeyMo duplicate-safe source-training candidates | 2,097 | Road-marking-positive images with boxes; no automatic primary label |
| Mendeley manhole and speed-breaker (exact-deduplicated, label-conflict holdout applied) | 807 | 660 manhole-cover and 147 speed-bump image-level supporting candidates; no boxes |
| **Total** | **12,490** | Not a final training split |

## Task eligibility

| Possible task support | Images | Meaning |
| --- | ---: | --- |
| Multi-class, multi-label, and object detection | 7,241 | SVRDD and GitHub pothole records have boxes |
| Multi-class and multi-label only | 624 | V1 pothole records have no boxes |
| Multi-class only | 1,721 | StreetSurfaceVis has surface labels but no boxes or complete multi-label truth |
| Multi-label and object detection | 2,097 | CeyMo confirms road-marking presence and boxes, but not a complete multi-class scene label |

The approved 155-image StreetSurfaceVis shadow subset is an explicit exception:
those existing eligible road-surface candidates also support the limited
multi-label pair `normal_asphalt;shadow` or `unpaved_road;shadow`. The separate
`docs/v2_shadow_multilabel_manifest.csv` records that overlay; it does not
duplicate images or claim complete multi-label truth for every condition.

Task eligibility does not mean the data is ready for training. Remaining label,
near-duplicate, imbalance, and split checks still apply.

## Provisional multi-class primary labels

| Primary label | Candidate images |
| --- | ---: |
| `crack` | 3,907 |
| `repaired_road` | 1,620 |
| `pothole` | 2,337 |
| `manhole_cover` | 1 |
| `normal_asphalt` | 791 |
| `unpaved_road` | 930 |
| `road_marking` | 0 |

The `manhole_cover` count of one is a serious feasibility warning. It does not
mean SVRDD contains only one manhole. The provisional one-label priority rule
selects pothole, crack, or repaired road before manhole when several conditions
appear in one image. As a result, manholes are hidden from the primary-label
count.

**Decision:** do not build the V2 multi-class training split from these primary
labels yet. A later task must either create single-condition image crops from
the audited boxes or define another defensible method that gives
`manhole_cover` enough honest primary examples.

CeyMo adds no row to the current multi-class counts. Its 2,097 accepted images
prove that a road marking is present, but they have not been exhaustively
reviewed for the other V2 conditions required by the one-label priority rule.

## Multi-label positive-image counts

One image may appear in more than one row of this summary:

| Positive condition | Images containing the condition |
| --- | ---: |
| `crack` | 4,253 |
| `repaired_road` | 2,077 |
| `manhole_cover` | 1,688 |
| `pothole` | 2,337 |
| `road_marking` | 2,097 |
| `shadow` | 155 |

These counts show that multi-label classification represents mixed-condition
images more honestly than the current single-label priority rule.

## Detection object counts

| Box label | Objects |
| --- | ---: |
| `crack` | 7,335 |
| `repaired_road` | 5,089 |
| `manhole_cover` | 2,517 |
| `pothole` | 4,740 |
| `road_marking` | 3,484 |

The 624 V1 pothole images are not included in the object count because they do
not have boxes.

## Exact-duplicate and separation checks

| Check | Result |
| --- | ---: |
| Candidate IDs | 11,683 unique |
| Candidate source paths | 11,683 existing files |
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
- GitHub pothole-detection: MIT licence is stated in the source repository;
  recheck before redistributing any files.
- StreetSurfaceVis: CC-BY-SA is stated on the official Zenodo record; recheck
  before redistribution.
- CeyMo: the official repository contains an MIT licence; confirm that it
  covers dataset-file redistribution before redistributing images.

The inventory contains paths and evidence only. It does not redistribute the
raw images.

## Remaining blockers

1. Resolve the single-label `manhole_cover` collapse before multi-class model
   construction.
2. Add or human-label the remaining look-alike conditions: shadow, puddle,
   and road stain.
3. Check near duplicates and source groups, not only byte-identical files.
4. Decide task-specific inclusion rules because V1 potholes cannot support
   object detection without boxes.
5. Create new leakage-safe train, validation, and protected-test splits.
6. Recalculate class balance after all exclusions and splitting.
7. Complete the full V2 Data Gate before training any V2 model.

## Current decision

**All currently accepted sources, including the audited GitHub pothole source
and duplicate-safe CeyMo road-marking records, are integrated. This is
pre-split evidence, not a training dataset. V2 training remains blocked.**
