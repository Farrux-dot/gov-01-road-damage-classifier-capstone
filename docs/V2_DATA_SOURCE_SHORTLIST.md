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
| [SVRDD_YOLO](https://huggingface.co/datasets/ShuoZheLi/SVRDD_YOLO) | Dataset card lists 8,000 images, 20,804 annotated objects, a total size of 3.92 GB, and YOLO-format annotations. Its classes include three crack types, potholes, manhole covers, and longitudinal/transverse patches. The card states CC BY 4.0. | `Pothole`, `Crack`, `Manhole`, `Repaired_road` | Object detection; multi-label after conversion | **Acquired and structurally audited on 2026-09-02.** V2 label conversion, visual sample review, and a new V2 split are still required before training. |
| [RDD2022 official dataset record](https://figshare.com/articles/dataset/RDD2022_-_The_multi-national_Road_Damage_Dataset_released_through_CRDDC_2022/21431547) | The official Figshare record lists CC BY 4.0. It reports 47,420 road images from six countries, over 55,000 damage instances, and four damage types: longitudinal crack, transverse crack, alligator crack, and pothole. The full archive is 12.36 GB. | `Pothole`, `Crack` | Object detection; multi-label after a documented label conversion | **Deferred.** Its host was too slow during the 2026-09-01 attempted download. Do not use the country links that returned HTTP 403. |
| [N-RDD2024 official dataset record](https://data.mendeley.com/datasets/27c8pwsd6v/5) | The official Mendeley record lists CC BY 4.0, ten road-condition labels, and a 6.58 GB complete download. | `Pothole`, `Crack`, `Manhole`, `Repaired_road`, `Road_marking` look-alikes | Object detection; multi-label after conversion | **Deferred.** The host throttled the complete download; it is not the first V2 acquisition. |
| [PaveBench](https://huggingface.co/datasets/VVQNN/PaveBench) | Dataset card lists 20,124 high-resolution 512 x 512 pavement images for its visual-perception subset; image-level labels, detection boxes, and segmentation masks; and CC BY-NC-SA 4.0. Its visual classes are pothole, three crack types, patch, and negative. It also retains hard distractors such as pavement stains, tree shadows, and road markings. | `Pothole`, `Crack`, `Repaired_road` (from `patch` after visual review), and candidate hard-negative images | Image classification and object-detection supplement | **Downloaded on 2026-09-06; structural preflight passed with warnings.** The downloaded classification and detection tasks contain 20,124 classification images and 11,857 readable detection images with valid COCO alignment. However, 22 exact duplicate groups cross the source detection splits. Do not use its supplied splits as V2 evaluation; rebuild a duplicate-free split later. It has no `Manhole`, `Unpaved_road`, `Shadow`, `Puddle`, `Road_stain`, or `Road_marking` ground-truth class. Do not turn its generic `negative` images into those labels automatically. Its non-commercial, share-alike licence must be retained in project documentation. |
| [RAD Road Anomaly Detection](https://www.kaggle.com/datasets/rohitsuresh15/radroad-anomaly-detection) | Public Kaggle version 3 lists the MIT licence. The extracted labelled image section contains 8,394 readable 1920 x 1080 images with matching YOLO files. The source classes are HMV, LMV, Pedestrian, RoadDamages, SpeedBump, and UnsurfacedRoad. | Candidate `Unpaved_road` only, after human confirmation of `UnsurfacedRoad` | Multi-class or multi-label supplement; its boxes are not suitable for a separate unpaved-surface object detector | **Downloaded and structurally audited on 2026-09-11.** Audit found 593 `UnsurfacedRoad` boxes in 539 images and 20 exact-duplicate groups crossing source splits. The source splits must not be reused. A deterministic 60-image source-training review is pending; RAD is not yet accepted into the V2 inventory. |
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

## Corrected multi-source V2 plan

No single reviewed source contains the full V2 label guide. The future V2
dataset must therefore be treated as separate, honest data pools rather than
one falsely complete dataset.

| Needed V2 condition | Current honest source position |
| --- | --- |
| `Pothole` | Available in audited SVRDD. PaveBench may later add high-resolution diversity after its own audit. |
| `Crack` | Available in audited SVRDD. PaveBench may later add high-resolution diversity after its own audit. |
| `Repaired_road` | Available in audited SVRDD. PaveBench `patch` may map here after visual and format audit. |
| `Manhole` | Available in audited SVRDD. PaveBench does not provide it. |
| `Unpaved_road` | RAD supplies 539 candidate images labelled `UnsurfacedRoad`, but a 60-image human review is still pending. The class remains blocked until that review confirms the mapping and image quality. |
| `Shadow`, `Puddle`, `Road_stain`, `Road_marking` | **Open gap.** These require explicit manual labels. PaveBench negative images are only candidates for manual review, not ground truth for a named look-alike label. |
| `Normal_asphalt` | **Open gap.** Must be manually reviewed as clear asphalt; it cannot be inferred from a generic negative label. |

The V1 Normal data is rejected for this purpose because its 64 x 64 images do
not have enough detail for a defensible clear-asphalt or look-alike decision.
See [`V2_V1_NORMAL_VISUAL_REVIEW.md`](V2_V1_NORMAL_VISUAL_REVIEW.md).

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

## Completed PaveBench crack-sample decision

On 2026-09-08, the deterministic crack-only review was finalized: 16 of 36
sampled images were marked `clear_keep` and 20 were marked
`unclear_exclude`. Because most reviewed images were not clear enough for the
proposed use, the PaveBench crack classification folders are **not approved for
automatic bulk inclusion**. See `docs/V2_PAVEBENCH_VISUAL_REVIEW.md` for the
per-category evidence and limitations.

## Completed PaveBench look-alike decision

The separate 60-image PaveBench negative sample was reviewed for the missing
look-alike classes. The reviewer confirmed that none of the sampled images
clearly represented `Shadow`, `Puddle`, `Road_marking`, `Road_stain`,
`Normal_asphalt`, or `Unpaved_road`. All 60 reviewed records are excluded and
zero were accepted. This decision applies to the reviewed sample only; it does
not turn the remaining generic negative images into named labels.

## RAD acquisition and audit decision

The RAD version 3 archive was downloaded on 2026-09-11. Only the labelled
image section was extracted; the 5.39 GiB raw-video section was skipped because
it is not required for the current label review. Structural checks passed for
all 8,394 images and YOLO label files. The audit also found 20 exact duplicate
groups crossing the supplier's train, validation, and test folders, so a later
V2 split must be rebuilt by content and source group.

Only the source class `UnsurfacedRoad` is being considered, as a possible map
to `Unpaved_road`. The broad `RoadDamages` label must not be converted into a
specific pothole or crack label. A deterministic 60-image review workbook was
prepared from source-training records only. No RAD image has entered the V2
candidate inventory and no model has been trained from RAD.

## Next approved task

Complete the 60-image RAD `UnsurfacedRoad` human review. Accept only images
where a person can clearly recognise an unpaved road; mark wrong or unclear
examples for exclusion. After the decisions are recorded, calculate the real
approval rate and decide whether RAD can become the `Unpaved_road` source. Do
not merge sources, build the final split, or train a model at this stage.
