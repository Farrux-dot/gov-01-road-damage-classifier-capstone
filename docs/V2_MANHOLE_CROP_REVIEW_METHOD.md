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
  --annotations data\raw\v2\svrdd\extracted\train\train.v2.jsonl `
  --images-root data\raw\v2\svrdd\extracted\train `
  --manifest <review-output>\manhole_crop_review_manifest.csv `
  --previews-dir <review-output>\previews `
  --report <review-output>\manhole_crop_review_report.json `
  --sample-size 60 `
  --seed 42
```

`<review-output>` is deliberately outside Git because the preview images and workbook are review artifacts, not source code.

## Current decision

**WAIT.** The 60-row workbook still requires human decisions. Do not create an accepted manhole crop set, construct a final split, or train a V2 model until the completed workbook is returned and validated.

## Limitations

- A source annotation can still be wrong even when it passes the automated prefilter.
- Cropping can remove useful road context.
- The first workbook covers 60 of 706 eligible candidates, not the entire pool.
- Approval confirms only that the crop is a useful manhole candidate; it does not prove model performance.
- The source card states CC BY 4.0; its terms must be rechecked before redistribution.
