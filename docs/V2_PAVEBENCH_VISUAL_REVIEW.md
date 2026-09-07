# V2 PaveBench Visual Label Review

## Purpose

This step prepares small sheets of real PaveBench images for a person to
inspect. It checks whether the visual content appears consistent with the
source folder name. It does not change any label automatically.

## Three sheets prepared

| Source folder | What the reviewer checks | V2 decision after review |
| --- | --- | --- |
| `pothole` | Does each image visibly contain a pothole? | Candidate for `Pothole` only if the sample looks correct. |
| `patch` | Does it show a repaired/filled road area rather than another road feature? | Candidate for `Repaired_road`; do not accept automatically. |
| `negative` | What kinds of non-target road scenes appear? | Keep as generic negative candidates only. Do not give named look-alike labels without explicit human annotation. |

## Review rule

For every sheet, record one of these conclusions:

- **Accept for later candidate pool** — examples visually fit the proposed purpose.
- **Reject from that candidate pool** — examples visibly do not fit.
- **Mixed or unclear** — keep the source separate and decide later image by image.

The review sheets are stored only in the ignored
`reports/v2_pavebench_review/` folder. They are reproducible from the raw
dataset and therefore are not committed to Git.

## Run command

```powershell
.\.venv\Scripts\python.exe src\review_pavebench_samples.py `
  --classification-dir data\raw\v2\pavebench\data\Distress_Classification `
  --output-dir reports\v2_pavebench_review `
  --samples-per-class 12 `
  --seed 42
```

## Boundary

This review does not remove the 22 exact duplicates found in PaveBench's
supplied detection splits. It does not create a combined SVRDD/PaveBench split
and does not make the project ready for V2 training.
