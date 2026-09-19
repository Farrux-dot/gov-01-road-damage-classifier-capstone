# V2 Kaggle Speed-Bump Train/Test Package Audit

- **Source:** [Speed Bump Dataset](https://www.kaggle.com/datasets/ziya07/speed-bump-dataset)
- **Licence record:** CC0 / Public Domain stated on the Kaggle dataset page; recheck before redistribution
- **Audit date:** 2026-09-19
- **Raw data changed:** No

## Verified results

- Readable labelled bump images: 4259
- Kept non-sequence, exact-unique train candidates: 1076
- Reserved supplied source-test images: 1277
- Excluded MVI sequence-risk train images: 1887
- Excluded redundant exact-duplicate train images: 19
- Held train images duplicated in source test: 0
- Exact duplicate groups across train and test: 81

## Decision boundary

Only retained train records can be considered for future V2 training. The supplied source-test folder is reserved and is never used for training or tuning. This audit only checks exact duplicates; it does not certify that visually similar video frames are independent.
