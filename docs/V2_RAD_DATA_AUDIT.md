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

## Human-review gate

A deterministic 60-image workbook was prepared from source `train` records only. It uses seed `42`, prefers one representative per recording group, and selects a large `UnsurfacedRoad` box inside each chosen group. The workbook shows both the full image with the supplied box and an enlarged crop.

Allowed decisions are `clear_unpaved_keep`, `not_unpaved_exclude`, and `unclear_exclude`. The 539 source-labeled images remain candidates only until this review confirms that the class matches our intended meaning.

## Current decision

RAD passes the file and annotation checks but remains at **needs review** because the class mapping needs human confirmation and 20 exact duplicate groups cross the supplier's splits. No RAD image has entered the V2 inventory, no final split has been created, and no model has been trained.

## Reproduction command

```powershell
.\.venv\Scripts\python.exe src\audit_rad.py `
  data\raw\v2\rad\extracted\images `
  --output reports\rad_structural_audit.json
```
