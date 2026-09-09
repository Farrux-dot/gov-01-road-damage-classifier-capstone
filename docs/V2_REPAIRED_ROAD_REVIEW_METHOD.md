# V2 SVRDD Repaired-Road Review Method

## Purpose

This audit checks whether the SVRDD `repaired_road` source label is suitable for the V2 experiment. It uses only `train.v2.jsonl`. SVRDD validation and test records are not used for filtering or selection.

The audit does not create a final train/validation/test split and does not measure model performance.

## Automatic prefilter

The source training annotations contain 5,089 repaired-road boxes. Each box receives a stable candidate ID containing the source split, image ID, class, and box index.

A candidate is held when:

- the target box is smaller than 28 pixels on its shortest side; or
- another labelled road condition materially overlaps the contextual crop.

The overlap rule holds a candidate when another condition occupies at least 10% of its own box inside the crop or at least 2% of the crop area.

| Prefilter result | Count |
|---|---:|
| Clear-context review candidates | 2,685 |
| Held because target is too small | 1,765 |
| Held because another condition enters the crop | 639 |
| Total repaired-road source boxes | 5,089 |

## Human review evidence

### Round 1

Round 1 sampled 60 clear-context candidates using seed `42`, balanced at 12 candidates from each SVRDD region.

- Workbook: `SVRDD_Repaired_Road_Sample_Review.xlsx`
- SHA-256: `0D47283748E1199F5E697E1EAFD4EDEA85DB9845789923869B610035FEF42748`

| Decision | Count |
|---|---:|
| `approve_repaired_road` | 51 |
| `reject_unclear` | 7 |
| `wrong_box` | 2 |

### Round 2

Round 2 reviewed 40 unused candidates:

- 20 additional Xicheng examples because Xicheng had the lowest Round 1 approval rate;
- 20 multi-patch examples, five each from Chaoyang, Dongcheng, Fengtai, and Haidian, to check source box completeness.

No source image or candidate ID was repeated from Round 1. Larger previews displayed the current target in green, other repaired-road boxes in blue, and other road-condition boxes in orange.

- Workbook: `SVRDD_Repaired_Road_Sample_Review_Round2.xlsx`
- SHA-256: `DD75F19D93F2418354E8CA74ABBE3BC59D4BFECDA35B4C89DBE7B16FC3EBAAB5`

All 40 Round 2 candidates were marked `approve_repaired_road`. There were no pending, invalid, or duplicate rows.

### Combined review result

| Decision | Count |
|---|---:|
| `approve_repaired_road` | 91 |
| `reject_unclear` | 7 |
| `wrong_box` | 2 |
| Total reviewed | 100 |

The 91% sample approval rate supports conditional use of the automatically filtered source label. It does not prove that every unreviewed source box is correct.

## Evidence levels and retained records

The manifests deliberately distinguish two evidence levels:

- **Human approved:** 91 candidates were individually inspected and approved.
- **Source-labelled and audit-supported:** 2,585 clear-context candidates were not individually inspected. They may remain candidates because the source annotation, automatic filters, and two sample reviews support the class.

The 2,676 retained records are candidates only. They are not a final training split.

| Training status | Count |
|---|---:|
| `retain_human_approved_candidate` | 91 |
| `retain_source_labeled_audit_supported_candidate` | 2,585 |
| `exclude_human_rejected` | 9 |
| `hold_target_too_small` | 1,765 |
| `hold_nearby_other_condition` | 639 |

Every record keeps `split_group_id = svrdd::train::<source_image_id>`. All boxes from the same original image must stay in the same future split to prevent data leakage.

## Repository evidence

- `docs/v2_svrdd_repaired_road_review_decisions.csv`: the 100 human decisions and their original geometry.
- `docs/v2_svrdd_repaired_road_candidate_manifest.csv`: all 5,089 source-training repaired-road boxes with audit status.
- `docs/v2_svrdd_repaired_road_keep_manifest.csv`: the 2,676 retained candidates.
- `docs/v2_svrdd_repaired_road_exclude_manifest.csv`: the 2,413 held or rejected candidates.

The Excel workbooks and preview images remain outside Git because they are large review artifacts.

## Reproduction command

```powershell
.\.venv\Scripts\python.exe -B src\finalize_v2_repaired_road_reviews.py `
  --annotations data\processed\v2\svrdd\annotations\train.v2.jsonl `
  --decisions docs\v2_svrdd_repaired_road_review_decisions.csv `
  --all-output docs\v2_svrdd_repaired_road_candidate_manifest.csv `
  --keep-output docs\v2_svrdd_repaired_road_keep_manifest.csv `
  --exclude-output docs\v2_svrdd_repaired_road_exclude_manifest.csv
```

The finalizer stops if a decision is pending or unsupported, a rejected row lacks a note, a candidate ID is duplicated, source geometry has changed, or a reviewed candidate is outside the SVRDD training split.

## Data Gate decision

**CONDITIONAL RETENTION.** Keep the 2,676 filtered candidates with their honest evidence labels. Do not describe all of them as human approved. Do not create a final split or train a V2 model until retained files and crop geometry are materialized and verified.

## Remaining limitations

- Only 100 of the 2,685 clear-context candidates were manually reviewed.
- A source annotation may still be wrong even after automatic filtering.
- Held mixed-condition crops could become useful later for multi-label training, but they are not approved by this step.
- Approval means the repaired-road label is visually credible; it does not prove detection accuracy.
- SVRDD licence and redistribution requirements must be checked before publishing source images.
