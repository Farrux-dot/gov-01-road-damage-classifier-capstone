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
- The metadata-only proposed split is 70% train (8,936), 15% validation
  (1,916), and 15% protected test (1,916), using seed 42.
- No final V2 image folders were copied or materialized by this split process.

The main evidence is `docs/V2_FINAL_DATA_AUDIT_AND_SPLIT_PLAN.md`,
`docs/v2_candidate_inventory.csv`, and
`docs/v2_multiclass_split_manifest.csv`.

## Data-quality gate: do not train yet

Exact-hash checks passed for the V2 candidate inventory: no duplicate SHA-256
groups and no source validation/test records were accidentally included.

However, the cross-split near-duplicate audit found:

- 2,487 suspicious cross-split pairs;
- 1,342 pairs needing a same-split holdout policy (distance 0–3);
- 413 different-label pairs needing label-conflict inspection.

The current V2 split is **not safe to materialize**. Before training or copying
V2 files, resolve confirmed near-duplicate families so they remain in one split
or are held out, regenerate the manifest, and rerun the audit. Keep the
protected test untouched during model selection.

Evidence: `docs/v2_cross_split_near_duplicate_pairs.csv` and
`reports/v2_cross_split_near_duplicate_audit.json`.

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

Perform a small, documented near-duplicate conflict-resolution task for the
V2 proposed split. Do not delete, move, regenerate, or train until the exact
candidate families and split policy are approved.
