# V2 Data Source Shortlist and Acquisition Plan

## Purpose and boundary

This is a source shortlist for the experimental V2 road-condition work on branch `codex/road-condition-v2`. It is **not** evidence that any V2 dataset has been downloaded, audited, or approved for training.

V1 data, V1 splits, V1 protected-test results, and the deployed V1 app remain unchanged.

## Decision: use a source combination, not one dataset

No reviewed source contains every V2 label. The chosen future V2 pool must combine:

1. a licensed road-damage source for potholes and cracks;
2. a licensed source or permission-based collection for repaired patches, unpaved roads, and road look-alikes; and
3. manual V2 labeling using `docs/V2_ROAD_CONDITION_LABELING_GUIDE.md`.

Images must not be downloaded into Git. Store raw archives and raw images in an ignored `data/raw/v2/` location only after recording the source, license, download date, and intended use.

## Reviewed candidates

| Candidate | Verified information | V2 labels it can help with | Suitable approach | Decision |
| --- | --- | --- | --- | --- |
| [SVRDD_YOLO](https://huggingface.co/datasets/ShuoZheLi/SVRDD_YOLO) | Dataset card lists 8,000 images, 20,804 annotated objects, a total size of 3.92 GB, and YOLO-format annotations. Its classes include three crack types, potholes, manhole covers, and longitudinal/transverse patches. The card states CC BY 4.0. | `Pothole`, `Crack`, `Manhole`, `Repaired_road` | Object detection; multi-label after conversion | **Selected first acquisition candidate.** It is a manageable labelled source for the first V2 audit. |
| [RDD2022 official dataset record](https://figshare.com/articles/dataset/RDD2022_-_The_multi-national_Road_Damage_Dataset_released_through_CRDDC_2022/21431547) | The official Figshare record lists CC BY 4.0. It reports 47,420 road images from six countries, over 55,000 damage instances, and four damage types: longitudinal crack, transverse crack, alligator crack, and pothole. The full archive is 12.36 GB. | `Pothole`, `Crack` | Object detection; multi-label after a documented label conversion | **Deferred.** Its host was too slow during the 2026-09-01 attempted download. Do not use the country links that returned HTTP 403. |
| [N-RDD2024 official dataset record](https://data.mendeley.com/datasets/27c8pwsd6v/5) | The official Mendeley record lists CC BY 4.0, ten road-condition labels, and a 6.58 GB complete download. | `Pothole`, `Crack`, `Manhole`, `Repaired_road`, `Road_marking` look-alikes | Object detection; multi-label after conversion | **Deferred.** The host throttled the complete download; it is not the first V2 acquisition. |
| [RAD Road Anomaly Detection](https://www.kaggle.com/datasets/rohitsuresh15/radroad-anomaly-detection) | The published description lists potholes, cracks, manholes, and unsurfaced roads. The licence was not verified during this shortlist review. | Potentially `Pothole`, `Crack`, `Manhole`, `Unpaved_road` | Possible multi-class or object-detection supplement | **Do not download yet.** Check the Kaggle licence and annotation format first. |
| Manually collected or permission-based images | License and consent depend on the individual source; must be recorded per image set. | `Shadow`, `Puddle`, `Road_marking`, `Road_stain`, `Repaired_road`, `Unpaved_road`, clean `Normal_asphalt` | All three V2 approaches after manual labeling | **Required supplement.** These look-alike categories are essential to prevent false pothole alerts. |

## How each model approach will receive data

### 1. Multi-class classification

Each image needs one primary label from the V2 labeling guide. The source annotation alone is not enough: an image with more than one condition must be reviewed and assigned one main label using the documented priority order.

### 2. Multi-label classification

Each image needs nine Yes/No values:

- pothole present
- crack present
- repaired patch present
- unpaved surface present
- shadow present
- puddle present
- manhole present
- road marking present
- road stain present

Existing object boxes can help establish some labels, but each image must still be reviewed for the visual look-alikes that source annotations may not include.

### 3. Object detection

The first object-detection pilot should use a source with genuine bounding boxes, such as RDD2022 or SVRDD_YOLO. The pilot must use a separate clean split created after duplicate and source-overlap checks. A source-provided train/validation/test split must not automatically be trusted as leak-free.

## Required source record before download

For every candidate used, record:

| Field | Required record |
| --- | --- |
| Source name and URL | Exact public page URL |
| Owner or publisher | Name shown on the source page |
| Licence | Exact licence name and link |
| Download date | Date acquired |
| Original annotation format | Image-level, YOLO boxes, COCO boxes, or another format |
| Intended V2 use | Training, validation, candidate pool, or manual review only |
| Restrictions | Attribution, share-alike, non-commercial, privacy, or other conditions |

## Data rules before modeling

1. Do not evaluate V2 with V1's protected test set.
2. Do not use pseudo-labels or augmented duplicates in the V2 protected test set.
3. Do not mix different source licences without documenting the combined-use implications.
4. Review and remove exact duplicates before splitting.
5. Split by source, location, route, or recording session where possible.
6. Ensure each label has enough varied examples before claiming that V2 can recognise it.
7. Record ambiguous images as `Unclear_exclude`; do not force them into a class.

## Next approved task

Acquire SVRDD_YOLO only. Save it under the ignored `data/raw/v2/svrdd/` location, then inspect its archive structure and run the V2 data audit. Do not use its supplied test split as V2's final protected test without duplicate and source-overlap checks.
