# V2 PaveBench Detection Label Review Data Gate

**Review date:** 2026-09-09  
**Scope:** PaveBench object-detection label and box quality  
**Status:** completed sample review; V2 training is not yet approved

## Purpose

This review checks whether PaveBench detection images visibly match their
provider labels and whether the provider's red object box points to the road
condition. It uses human decisions from two reproducible sample rounds. It
does not change raw images, approve every unreviewed image, create a final V2
split, or train a model.

## Evidence used

- Round 1: 12 sampled records from each of `alligator`, `crack`, `patch`, and
  `pothole` (48 records).
- Round 2: 50 new `alligator` and 50 new `crack` records, selected with seed
  `84` after excluding the Round 1 files (100 records).
- Combined manifest: `docs/v2_pavebench_detection_review_manifest.csv`.
- Total reviewed: 148 unique sample IDs and 148 unique source files.

The image workbooks are not tracked because they contain embedded raw dataset
images. The compact CSV manifest preserves the decisions and safe relative
source paths without committing the images themselves.

## Human decision meanings

- `approve`: the visible condition matches the provider label and the box is
  acceptable.
- `unclear_exclude`: the condition cannot be identified confidently; exclude
  the record.
- `wrong_label`: the visible road condition does not match the provider label;
  exclude the record.
- `wrong_box`: the label may be plausible, but the provider box is wrong;
  exclude the record from detection work.

## Combined results

| Provider class | Reviewed | Approved | Unclear | Wrong label | Wrong box | Approved share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `alligator` | 62 | 55 | 6 | 0 | 1 | 88.7% |
| `crack` | 62 | 43 | 13 | 6 | 0 | 69.4% |
| `patch` | 12 | 11 | 1 | 0 | 0 | 91.7% |
| `pothole` | 12 | 4 | 6 | 2 | 0 | 33.3% |
| **Total** | **148** | **113** | **26** | **8** | **1** | **76.4%** |

These percentages describe only the reviewed samples. They are not model
metrics and do not prove that the same percentages apply to every unreviewed
PaveBench image.

## Data Gate decisions

### `alligator`

The reviewed sample is comparatively strong. The label may continue as a
conditional candidate for the V2 `Crack` class, but the approved sample does
not prove that every unreviewed record is correct. Before use, selected records
still require exact-deduplication, source traceability, and a new leakage-safe
split.

### `crack`

Do not bulk-accept the source class. Only individually reviewed approved
records may enter a candidate pool at this stage. The unclear and wrong-label
records show that the source name alone is not enough evidence.

### `patch`

Keep the 11 individually approved records as candidates for
`Repaired_road`. Do not automatically accept the full PaveBench patch class
from this small sample.

### `pothole`

Do not use the PaveBench pothole class for the V2 candidate pool. The detection
sample approved only 4 of 12 records, and the separate classification-image
review approved 0 of 12. Use only the 624 eligible V1 **training** pothole
images as the current pothole source. V1 validation and protected-test images
remain reserved and must not enter V2 training.

## Manifest actions

The combined manifest preserves every human decision. Its `record_action`
column applies these rules:

- approved Alligator, Crack, and Patch records become reviewed candidates;
- unclear, wrong-label, and wrong-box records are excluded;
- every reviewed PaveBench pothole record is excluded by class policy, even if
  that individual record was marked `approve`;
- no raw image is copied, deleted, or relabelled by the manifest.

This produces 109 reviewed candidate records: 55 Alligator, 43 Crack, and 11
Patch. It does not provide enough examples by itself for final V2 training.

## Evidence-quality notes

The original Round 1 workbook contains two preserved issues:

1. `alligator_01` is `unclear_exclude` but has no reviewer note.
2. `alligator_09` is recorded as `wrong_box`, while its note says only normal
   asphalt is visible. The manifest keeps the original decision and flags the
   inconsistency instead of silently rewriting human evidence.

Both records are excluded, so neither issue adds an unsafe candidate image.

## Remaining blockers before V2 training

1. Build one source-traceable candidate inventory across the approved sources.
2. Obtain or human-label clear examples for remaining road-condition and
   look-alike classes such as shadow, puddle, stain, road marking, normal
   asphalt, and unpaved road.
3. Remove exact and near duplicates before splitting.
4. Create new train, validation, and protected-test splits without source or
   duplicate leakage.
5. Recheck class counts and imbalance after cleaning.
6. Complete and document the full V2 Data Gate before training any V2 model.

## Current decision

**PaveBench detection sample review is complete, but the full V2 Data Gate
remains open. Do not train V2 yet.**
