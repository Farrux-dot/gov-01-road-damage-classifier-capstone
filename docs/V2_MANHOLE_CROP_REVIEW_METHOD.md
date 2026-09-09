# V2 SVRDD Manhole Crop Review Method

## Purpose

The V2 candidate inventory contains 1,688 SVRDD source-training images with at least one `manhole_cover` label and 2,517 manhole boxes. However, the provisional one-label priority rule assigns only one complete image to the primary `manhole_cover` class because cracks, potholes, or repaired-road labels usually occur in the same image.

This review tests a narrow solution: use the existing manhole boxes to propose smaller image crops in which a manhole cover is the main visible road condition. The crops are **candidates for human review only**. They are not automatically accepted as training data.

## Data boundary

- Source used: SVRDD_YOLO source `train` split only.
- Reserved SVRDD `validation` and `test` records are not read or shown.
- V1 validation and protected-test images are not used.
- Raw images are read but never changed.
- No final V2 split is created and no model is trained by this workflow.

## Automated prefilter

The generator performs these steps for every source-training `manhole_cover` box:

1. Reject any annotation file whose name is not `train.v2.jsonl`.
2. Build a square crop centered around the box, using 2.5 times the longer box side and a minimum crop side of 96 pixels.
3. Shift the crop when necessary so it remains inside the source image.
4. Hold a candidate when the manhole box's shortest side is less than 12 pixels because the target is likely too small for a reliable visual decision.
5. Hold a candidate when a non-manhole condition materially enters the crop. Material overlap means at least 10% of the other box or at least 2% of the proposed crop.
6. Send the remaining candidates to human visual review. Automated filtering does not approve a label.

## Actual prefilter result

| Result | Count |
|---|---:|
| Manhole boxes found | 2,517 |
| Held because target is too small | 1,132 |
| Held because another labelled condition enters the crop | 679 |
| Eligible for visual review | 706 |
| Selected for the first review workbook | 60 |

The sample uses random seed `42` and contains 12 candidates from each source region: Chaoyang, Dongcheng, Fengtai, Haidian, and Xicheng.

## Human review decisions

The workbook allows one decision per row:

- `approve_manhole`: the green target is clearly a manhole cover and the proposed crop is useful.
- `reject_not_manhole`: the green target is not a manhole cover.
- `reject_unclear`: the object is too small, blurry, obstructed, or otherwise uncertain.
- `reject_mixed_condition`: another road condition is still too important in the crop.
- `wrong_box`: the annotation box is badly positioned.

Use `approve_manhole` only when the object is clear. Shadows, puddles, stains, road markings, repairs, unclear objects, or mixed-condition crops must not be approved as manholes.

## Reproduction command

From the repository root:

```powershell
.\.venv\Scripts\python.exe -B src\build_v2_manhole_crop_review.py `
  --repo-root . `
  --annotations data\processed\v2\svrdd\annotations\train.v2.jsonl `
  --images-root data\raw\v2\svrdd\extracted\train `
  --manifest <review-output>\manhole_crop_review_manifest.csv `
  --previews-dir <review-output>\previews `
  --report <review-output>\manhole_crop_review_report.json `
  --sample-size 60 `
  --seed 42
```

`<review-output>` is deliberately outside Git because the preview images and workbook are review artifacts, not source code.

## Completed review result

The 60-row workbook was completed and validated on 2026-09-09.

- Reviewed workbook: `SVRDD_Manhole_Crop_Review.xlsx`
- Reviewed workbook SHA-256: `98B708E64D8A0253DE9594BD56D6462A23219FB8798C4AD2F7F2262C0B630660`

| Human decision | Count |
|---|---:|
| `approve_manhole` | 50 |
| `reject_unclear` | 10 |
| Pending or unsupported decisions | 0 |

All rejected rows contain reviewer notes. Candidate IDs are unique, and every source path remains inside the SVRDD source training split.

The reviewer reported that the small source resolution made several manholes difficult to recognize. The target-size evidence supports that concern:

- Among the 50 approved candidates, the target minimum side ranges from 12 to 68 pixels, with a median of 20 pixels.
- Of the approved candidates, 24 have a target smaller than 20 pixels and 15 are smaller than 16 pixels.
- Nine of the ten unclear rejections have a target smaller than 20 pixels.

The decision manifest therefore marks all 50 approvals as `retain_candidate_not_training_ready` and adds the evidence flag `low_resolution_review_difficulty`. The ten unclear records are excluded from the candidate pool.

## Current decision

**CONDITIONAL RETENTION.** Keep the 50 human-approved records as source-traceable candidates, not final training data. Do not create a final split or train a V2 model from them yet. First address whether the source resolution is adequate for the intended high-resolution upload workflow or obtain clearer manhole examples.

## Round 2 clearer-target review

The first review showed that simply enlarging a small crop does not restore missing visual detail. A second review workbook was therefore generated from unused SVRDD source-training candidates with a stricter size rule.

- All 60 candidates from Round 1 are excluded by candidate ID.
- The target box must be at least 28 pixels on its shortest side.
- The 28-pixel cutoff leaves at least 12 unused eligible candidates in every source region. A 32-pixel cutoff was not used because only six unused Chaoyang candidates met it.
- The deterministic Round 2 sample contains 60 candidates: 12 each from Chaoyang, Dongcheng, Fengtai, Haidian, and Xicheng.
- Selected targets range from 28 to 57 pixels on their shortest side.
- Human review was completed on 2026-09-09.

| Human decision | Count |
|---|---:|
| `approve_manhole` | 51 |
| `reject_unclear` | 7 |
| `reject_not_manhole` | 2 |
| Pending or unsupported decisions | 0 |

- Reviewed workbook: `SVRDD_Manhole_Crop_Review_Round2.xlsx`
- Reviewed workbook SHA-256: `CFBC39FCC918F1F5A26F209A287961706FD07D0273D2E0C35DD2FCB514B09966`
- Every rejected row has a reviewer note.
- Candidate IDs are unique, all source paths remain inside the SVRDD source training split, and no Round 2 candidate repeats a Round 1 candidate ID.
- The reviewer excluded examples affected by darkness, shadows, unclear objects, or incorrect source annotations instead of forcing uncertain manhole labels.
- The 51 approvals remain candidates only. They are not part of a final split and have not been used to train a model.

Round 2 can be reproduced with:

```powershell
.\.venv\Scripts\python.exe -B src\build_v2_manhole_crop_review.py `
  --repo-root . `
  --annotations data\processed\v2\svrdd\annotations\train.v2.jsonl `
  --images-root data\raw\v2\svrdd\extracted\train `
  --manifest <review-output>\review_manifest_round2.csv `
  --previews-dir <review-output>\previews `
  --report <review-output>\review_report_round2.json `
  --sample-size 60 `
  --seed 42 `
  --exclude-manifest docs\v2_svrdd_manhole_crop_review_manifest.csv `
  --minimum-review-target-side 28
```

## Consolidated approved candidates

The two completed review rounds contain 120 reviewed crops in total:

| Result | Count |
|---|---:|
| Approved manhole candidates | 101 |
| Unclear exclusions | 17 |
| Not-manhole exclusions | 2 |
| Unique source images among approvals | 97 |

The approved-only manifest is `docs/v2_svrdd_manhole_approved_manifest.csv`. It joins each human decision to its generated target box and crop coordinates, so the accepted crop can be reproduced from the unchanged raw image.

Four original road images contribute two approved crops each. The manifest therefore includes `split_group_id`. Every crop from the same original road image must stay in the same future train, validation, or test split. This prevents the model from seeing one crop from an image during training and a nearly identical crop from the same image during evaluation.

Round 1's 50 approvals keep the flag `low_resolution_review_difficulty`. Round 2's 51 approvals keep the flag `clearer_target_round2_review`. All 101 rows have the status `approved_candidate_not_final_split`; approval does not mean that a final V2 dataset or trained model already exists.

The approved manifest can be rebuilt after the two generated review manifests are available outside Git:

```powershell
.\.venv\Scripts\python.exe -B src\finalize_v2_manhole_reviews.py `
  --round1-decisions docs\v2_svrdd_manhole_crop_review_manifest.csv `
  --round1-generated <round1-review-output>\manhole_crop_review_manifest.csv `
  --round2-decisions docs\v2_svrdd_manhole_crop_review_round2_manifest.csv `
  --round2-generated <round2-review-output>\review_manifest_round2.csv `
  --approved-output docs\v2_svrdd_manhole_approved_manifest.csv
```

The finalizer stops when a review is incomplete, a rejected row has no note, candidate IDs overlap between rounds, generated crop geometry is missing, or a source path leaves the SVRDD source-training boundary.

## Limitations

- A source annotation can still be wrong even when it passes the automated prefilter.
- Cropping can remove useful road context.
- The completed workbook covers 60 of 706 eligible candidates, not the entire pool.
- The two review rounds cover 120 candidate boxes, not all 706 candidates eligible after automated filtering.
- Low-resolution targets can be difficult for a human to verify and may not represent the intended high-resolution user images.
- Approval confirms only that the crop is a useful manhole candidate; it does not prove model performance.
- The source card states CC BY 4.0; its terms must be rechecked before redistribution.
