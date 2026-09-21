# PROJECT HANDOFF — GOV-01 Capstone

**Working repository:** `D:\Github\gov-01-road-damage-classifier-capstone`  
**Branch:** `codex/road-condition-v2`  
**Recovery date:** 2026-09-21

## Workspace rule

Use this D: checkout for all future work. Do not work in, inspect for changes,
or add files to the separate C: checkout at
`C:\Users\FarruxHP_2000\Documents\GitHub\gov-01-road-damage-classifier`.

## V1: assessed baseline (frozen)

V1 remains the assessed binary `Normal` versus `Pothole` classifier on `main`.
The selected model is `mobilenetv2_frozen_v4`; its protected-test Macro F1 is
`0.939901` and accuracy is `0.950820` on 183 images. The V1 candidate was
locked before its one protected-test evaluation. Do not tune, retrain,
reselect, or retest V1.

Evidence: `reports/model_gate.md`, `reports/experiment_record.csv`,
`artifacts/mobilenetv2_frozen_v4_config.json`, and
`docs/RESPONSIBLE_AI_AND_LIMITATIONS.md`.

## V2: current work

V2 is a separate multi-class road-condition data-preparation experiment. It
does not replace V1 and no V2 model has been trained.

- Candidate inventory: 14,865 source-traceable image records.
- Eligible proposed multi-class candidates: 12,768.
- Proposed labels: crack, pothole, repaired road, normal asphalt, speed bump,
  manhole cover, and unpaved road.
- The original metadata-only split used seed 42. It has now been replaced by
  the near-duplicate-resolved final metadata manifest: 9,452 training, 1,658
  validation, 1,654 protected-test, and four excluded label-conflict records.
- No final V2 image folders were copied or materialized by this split process.

The main evidence is `docs/V2_FINAL_DATA_AUDIT_AND_SPLIT_PLAN.md`,
`docs/v2_candidate_inventory.csv`, and
`docs/v2_multiclass_split_manifest.csv`.

## Data-quality gate: do not train yet

Exact-hash checks passed for the V2 candidate inventory: no duplicate SHA-256
groups and no source validation/test records were accidentally included.

The cross-split near-duplicate audit found 911 suspicious pairs involving
1,088 images. All were reviewed and resolved into 375 confirmed exact-duplicate
families. Same-label families were placed in training only. Two families had
conflicting labels (`pothole` / `crack` and `crack` / `repaired_road`), so their
four records are excluded rather than relabeled.

The final manifest has zero remaining cross-split duplicate pairs and no
remaining review items. It is still metadata only: do not copy, link, move, or
delete images without a separate approved materialization task. Keep the
protected test untouched during model selection.

Evidence: `docs/v2_cross_split_near_duplicate_pairs_reviewed.csv`,
`docs/v2_multiclass_split_manifest_near_duplicate_final.csv`, and
`docs/V2_FINAL_DATA_AUDIT_AND_SPLIT_PLAN.md`.

## Important scope boundaries

- The historical `experiment_dataset_v2_finetuning` binary experiment is
  closed after a weak protected test; do not reopen it.
- PaveBench, RAD, Deep Pavements, and CoCGRCDD are retired from the current
  V2 candidate inventory.
- Raw data, archives, generated image folders, model binaries, secrets, and
  API keys remain out of Git.
- Object-detection annotations are incomplete for many image-level candidates;
  do not claim a detection-ready dataset.

## Safest next task

Review and document whether all V2 Data Gate requirements are now satisfied.
Do not materialize the split, delete or move images, or train a V2 model unless
that separate next step is explicitly approved.
