# Project Status

## Project

GOV-01 Road Damage Image Classifier

## Current stage

Preparing for Data Audit (Module 8)

## Completed

- Selected the GOV-01 Road Damage Image Classification scenario.
- Defined the initial scope: binary `Normal` vs. `Pothole` image classification for report triage.
- Created the project repository and initial code/documentation structure.
- Selected a public Kaggle dataset candidate and documented that data files will not be committed to Git.

## Current task

Prepare the data-audit workflow before analysing the downloaded dataset.

## Next

- Download and extract the selected dataset into `data/raw/`.
- Run `src/audit_dataset.py` to inspect class counts, corrupt images, duplicates, splits, and possible leakage.
- Record only real audit findings in the project documentation.

## Known problems / blockers

- The dataset has not yet been downloaded and audited.
- No model has been trained; there are no evaluation results yet.
