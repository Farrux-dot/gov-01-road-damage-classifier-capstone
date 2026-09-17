# V2 Data Source Shortlist

**Updated:** 2026-09-17
**Rule:** only documented, still-available sources may enter the V2 candidate
inventory. Raw images and archives remain Git ignored.

## Integrated sources

| Source | URL | Current use | Important boundary |
| --- | --- | --- | --- |
| SVRDD YOLO | https://huggingface.co/datasets/ShuoZheLi/SVRDD_YOLO | Boxes for pothole, crack, manhole cover, and repaired road | Only source-training records are candidates; source validation/test remain reserved. |
| V1 Kaggle pothole dataset | https://www.kaggle.com/datasets/abhinavkulshreshth/pothole-detection-dataset | Image-level pothole candidates | Only clean V1 training potholes are eligible; no boxes. |
| GitHub pothole-detection | https://github.com/jaygala24/pothole-detection | Pothole boxes | 1,241 approved records and 4,061 valid boxes; unsplit source collection. |
| StreetSurfaceVis | https://zenodo.org/records/11449977 | Normal asphalt and unpaved road | Image-level labels only; non-training source records remain excluded. |
| CeyMo | https://github.com/oshadajay/CeyMo | Road-marking boxes | Road marking is positive evidence only; other conditions are not exhaustively labelled. |

## Deferred sources

| Source | URL | Reason |
| --- | --- | --- |
| RDD2022 | https://figshare.com/articles/dataset/RDD2022_-_The_multi-national_Road_Damage_Dataset_released_through_CRDDC_2022/21431547 | Official archive download was throttled; do not use until a new official access route is verified. |
| N-RDD2024 | https://data.mendeley.com/datasets/27c8pwsd6v/5 | Not downloaded or audited for this project. |

## Missing-label rule

Shadow, puddle, and road stain remain open gaps. A future source must document
its licence, intended V2 label, and how its images are verified before it is
added. Generic negative images are not ground truth for these conditions.

## Current decision

The sources above form a pre-split candidate pool only. No V2 train,
validation, or protected-test split has been created, and no V2 model has been
trained.
