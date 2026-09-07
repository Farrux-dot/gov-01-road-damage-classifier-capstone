# V2 PaveBench Visual Label Review

## Purpose

This step prepares enlarged sheets of real PaveBench images for a person to
inspect. Each review image is shown at up to its original 512 x 512 size, so a
contact sheet does not reduce a 512 x 512 source image to a tiny preview. It
checks whether the visual content appears consistent with the source folder
name. It does not change any label automatically.

## Supported enlarged review sheets

| Source folder | What the reviewer checks | V2 decision after review |
| --- | --- | --- |
| `pothole` | Does each image visibly contain a pothole? | Mark each image `clear_keep` or `unclear_exclude`; do not decide for the whole dataset at once. |
| `patch` | Does it show a repaired/filled road area rather than another road feature? | Mark each image `clear_keep` or `unclear_exclude`; only a clear image can later be considered for `Repaired_road`. |
| `negative` | What kinds of non-target road scenes appear? | Mark each image `clear_keep` or `unclear_exclude`. A clear image is still generic negative only, not a named look-alike label. |
| `alligator_crack` | Is a connected, web-like crack pattern clearly visible? | Candidate for the V2 label `Crack` only after individual review. |
| `longitudinal_crack` | Is a crack running mainly along the road direction clearly visible? | Candidate for the V2 label `Crack` only after individual review. |
| `transverse_crack` | Is a crack running mainly across the road direction clearly visible? | Candidate for the V2 label `Crack` only after individual review. |

## Review rule

For every sheet, record one of these conclusions:

- **Accept for later candidate pool** — examples visually fit the proposed purpose.
- **Reject from that candidate pool** — examples visibly do not fit.
- **Mixed or unclear** — keep the source separate and decide later image by image.

The review sheets are stored only in the ignored
`reports/v2_pavebench_review/` folder. They are reproducible from the raw
dataset and therefore are not committed to Git.

For this project, `unclear_exclude` means: do not use that individual image in
any V2 pool. It does not say that the original source label is false.

## Run command

```powershell
.\.venv\Scripts\python.exe src\review_pavebench_samples.py `
  --classification-dir data\raw\v2\pavebench\data\Distress_Classification `
  --output-dir reports\v2_pavebench_full_size_review `
  --samples-per-class 12 `
  --seed 42
```

The sheets use two columns and preserve up to 512 x 512 pixels per image. Open
the saved PNG at 100% size and scroll through it. Do not judge the source from
only a reduced browser preview.

The same folder receives `human_review_queue.csv`. Open it in Excel and change
only the `human_decision` column for each displayed image:

- `clear_keep` — you can clearly see the source condition and its proposed use
  is honest.
- `unclear_exclude` — you cannot confidently identify the condition, so the
  image must not enter a V2 data pool.

Use `reviewer_note` only for a short reason, such as `clear pothole` or
`surface texture only`. Leave no row as `pending` before a later data-pool
decision.

## Crack-only review command

```powershell
.\.venv\Scripts\python.exe src\review_pavebench_samples.py `
  --classification-dir data\raw\v2\pavebench\data\Distress_Classification `
  --output-dir reports\v2_pavebench_crack_review `
  --samples-per-class 12 `
  --seed 42 `
  --classes alligator_crack longitudinal_crack transverse_crack
```

All three source crack types remain separate in the audit record but map to
the single proposed V2 condition `Crack`. An image is accepted only when the
crack is clear to the human reviewer.

## Finalize a completed crack review

After every CSV row is changed from `pending` to either `clear_keep` or
`unclear_exclude`, run:

```powershell
.\.venv\Scripts\python.exe src\finalize_pavebench_review.py `
  --review-csv reports\v2_pavebench_crack_review\human_review_queue.csv `
  --output-dir reports\v2_pavebench_crack_review
```

The command stops if even one decision is missing, uses an unsupported word,
or repeats an image path. When all rows are valid, it creates one manifest for
clear images and another for excluded images. It does not copy or relabel any
raw image and it does not create train/validation/test splits.

## Boundary

This review does not remove the 22 exact duplicates found in PaveBench's
supplied detection splits. It does not create a combined SVRDD/PaveBench split
and does not make the project ready for V2 training.
