# RAD Road Anomaly Detection Data Audit

**Audit date:** 2026-09-11  
**Training status:** not approved  
**Source:** [RAD Road Anomaly Detection on Kaggle](https://www.kaggle.com/datasets/rohitsuresh15/radroad-anomaly-detection)

## Why this source was checked

The current V2 pool has no accepted `Unpaved_road` examples. Public RAD version 3 advertises an `UnsurfacedRoad` class and uses the MIT licence. It was downloaded as a candidate source for that missing V2 condition.

The raw 7.31 GiB ZIP, extracted files, and review workbook are Git-ignored. Only the audit method and written evidence belong in Git.

## Safe extraction decision

| Archive section | Files | Size | Decision |
| --- | ---: | ---: | --- |
| Labeled images and YOLO text files | 16,789 | 1.92 GiB | Extracted for audit |
| Videos without audio | 364 | 5.39 GiB | Not extracted; not needed for the current label audit |

## Source labels and mapping boundary

The supplied `data.yaml` defines `HMV`, `LMV`, `Pedestrian`, `RoadDamages`, `SpeedBump`, and `UnsurfacedRoad`. Only `UnsurfacedRoad` is a proposed mapping to V2 `Unpaved_road`. The broad `RoadDamages` class cannot honestly be converted into one specific V2 damage condition without more information.

## Structural audit results

| Check | Real result |
| --- | ---: |
| Readable JPEG images | 8,394 / 8,394 |
| Matching YOLO label files | 8,394 / 8,394 |
| Invalid YOLO rows | 0 |
| Image resolution | 1,920 x 1,080 for all images |
| Empty label files | 91 |
| `UnsurfacedRoad` boxes | 593 |
| Images containing `UnsurfacedRoad` | 539 |
| Exact duplicate image groups | 49 |
| Exact duplicate groups crossing supplied splits | 20 |

The supplier's train/validation/test division must not become our final V2 split because exact duplicate images cross those folders. Related frames and duplicates must remain in one future group.

## Human-review result

A deterministic 60-image workbook was prepared from source `train` records only. It uses seed `42`, selects a large `UnsurfacedRoad` box, and shows both the full image and an enlarged crop. The completed workbook contains 33 preliminary `clear_unpaved_keep` choices, 26 `not_unpaved_exclude` choices, and one pending choice.

The sample contains 38 recording groups, with 16 groups represented more than once. Although there are no exact duplicate files in the workbook, a difference-hash check found eight highly similar same-recording pairs.

The review also exposed a semantic mismatch. Many scenes show asphalt as the main driving surface while the source box marks only a small unsurfaced shoulder or road-edge area. The earlier review wording was too broad because it did not require the main drivable surface to be unpaved. See `docs/V2_RAD_VISUAL_REVIEW.md`.

## Current decision

RAD passes the file and annotation checks but is **rejected for the current V2 `Unpaved_road` label**. The source `UnsurfacedRoad` boxes may identify localized dirt shoulders beside asphalt roads, so they do not reliably mean that the whole road is unpaved. The 33 preliminary keep choices are preserved as review history but are not accepted into the V2 inventory. No final split has been created and no model has been trained.

## Reproduction command

```powershell
.\.venv\Scripts\python.exe src\audit_rad.py `
  data\raw\v2\rad\extracted\images `
  --output reports\rad_structural_audit.json
```
