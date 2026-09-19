# V2 Kaggle Speed-Bump Source Audit

- **Source:** [Speed Bump Dataset](https://www.kaggle.com/datasets/ziya07/speed-bump-dataset)
- **Licence record:** CC0 / Public Domain stated on the Kaggle dataset page; recheck before redistribution
- **Audit date:** 2026-09-19
- **Raw data changed:** No

## Verified results

- Readable labelled images: 1000
- Kept non-sequence speed-bump candidates: 125
- Excluded MVI sequence-risk bump images: 106
- Excluded redundant exact-duplicate bump images: 19
- Exact duplicate groups: 20

## Decision boundary

This audit uses only source-labelled `bump` images without the numbered `MVI_...` recording-frame pattern. The source `crack`, `potholes`, and `road` folders are deliberately not added by this task. No bounding boxes or official source splits are available. The kept records are pre-split supporting candidates only; they require a final V2 split and visual sanity review before training.
