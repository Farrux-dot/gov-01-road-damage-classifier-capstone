# V2 N-RDD2024 Expansion Split Audit

**Audit date:** 2026-10-01  
**Stage:** data preparation complete; no model training started

## Purpose

This document records the new, separate multi-label dataset built after the
N-RDD2024 audit. Its purpose is to add strong, machine-annotated examples of
`crack`, `pothole`, `repaired_road`, and `manhole_cover` without changing the
earlier multi-label experiment or reusing its already-observed test set.

An image can have more than one condition. For example, a road image can be
positive for both crack and pothole.

## Combined dataset

The expansion combines the previously audited multi-label coverage pool with
the 23,433 N-RDD2024 training/validation records. It contains **39,617**
records across twelve source datasets.

N-RDD2024 provides a complete Yes/No answer only for four conditions:
`crack`, `pothole`, `repaired_road`, and `manhole_cover`. For its other three
conditions (`unpaved_road`, `road_marking`, and `speed_bump`), the value stays
unknown. Unknown does not mean No: those labels are excluded from the later
loss and score for that image.

## Full safety audit

Every record in the combined pool was opened and fingerprinted before the
split was created.

| Check | Result |
| --- | ---: |
| Source records | 39,617 |
| Readable images | 39,617 |
| Unreadable images | 0 |
| Exact duplicate groups | 5 |
| Records in exact duplicate groups | 10 |
| Likely near-duplicate pairs | 3,493 |
| Safe split groups | 37,218 |
| Records linked to another image | 3,771 |
| Largest linked group | 102 images |

Exact duplicates and likely near-duplicates were not deleted. Instead, every
linked family received one split-group ID and was placed entirely in one
split. This prevents the model from training on one version of an image and
being evaluated on a very similar version.

## New split

| Split | Images | Purpose |
| --- | ---: | --- |
| Train | 31,660 | Teach the model |
| Validation | 3,979 | Compare training choices and calibrate thresholds |
| Test | 3,978 | One final evaluation only, after a new model is locked |

The new test split is separate from every earlier V2 test result. It has not
been used for model selection, threshold selection, or training.

## Evidence available in each split

The table shows positive examples where the source actually knows that label.

| Condition | Train | Validation | New test |
| --- | ---: | ---: | ---: |
| Crack | 19,601 | 2,450 | 2,450 |
| Pothole | 4,453 | 557 | 557 |
| Repaired road | 3,720 | 465 | 465 |
| Manhole cover | 5,179 | 647 | 647 |
| Unpaved road | 1,091 | 136 | 136 |
| Road marking | 1,855 | 232 | 231 |
| Speed bump | 984 | 124 | 123 |

## Materialization result

The new data is stored outside Git at:

```text
data/processed/v2_multilabel_n_rdd_expansion/
```

All 39,617 images were copied from their sources and verified byte-for-byte
with SHA-256 checksums. Raw images, raw XML files, the previous processed
dataset, model files, and previous reports were not changed.

## Remaining boundary

This completes data preparation, not training. A new multi-label model must
use masked loss and masked scoring so that source-unknown labels are not
mistaken for negative examples. The next training run must use this new split
and must leave `test/` untouched until model selection is complete.
