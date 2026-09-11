# V2 Repaired-Road Deduplication and Quality Review

## Purpose

This step prevents identical repaired-road crop content from being counted more than once and prepares a manageable visual review of the remaining unique, source-labelled candidates.

It does **not** delete crop files, create the final V2 split, or train a model.

## Exact deduplication rule

1. Group materialized crop records by their SHA-256 image checksum.
2. Keep one record from each exact-content group.
3. If a group contains a human-approved record, prefer that record as the keeper.
4. Otherwise, keep the alphabetically first candidate ID so the result is repeatable.
5. Block automatically if identical content crosses an original source-image split group.
6. Record every redundant row in a separate exclusion manifest; do not delete its JPEG file.

Outputs:

- `docs/v2_svrdd_repaired_road_unique_manifest.csv`
- `docs/v2_svrdd_repaired_road_duplicate_exclusions.csv`

## Focused visual-quality review

The new review checks candidates that were not individually reviewed before. It samples only unique crops with the honest status `retain_source_labeled_audit_supported_candidate`.

The deterministic sample uses seed `42` and includes four crops from each combination of:

- five SVRDD regions;
- three crop-size bands: 128-191 pixels, 192-383 pixels, and 384 pixels or larger.

This creates 60 review rows. Each row comes from a different original source image. The Excel workbook embeds a preview and outlines the intended repaired-road annotation in green.

Allowed reviewer decisions:

- `approve_repaired_road`
- `reject_not_repaired_road`
- `reject_unclear`

Rejected rows require a short note. The review is evidence about the sampled unique crops; it is not a model score and does not prove that every unreviewed crop is correct.

## Completed review result

The 60-row review was completed on 2026-09-10:

- 51 crops were approved as visible repaired-road examples;
- 9 crops were rejected as unclear;
- no rows remained pending.

The nine unclear examples were excluded because the repaired area could not be
confirmed reliably by a human reviewer. The recorded reasons were one bus
shadow, three cases described as invisible to the human eye, and five cases
where the asphalt colour hid the repaired area.

These results apply only to the 60 reviewed samples. The 51 approvals strengthen
their evidence status, while the 9 unclear crops are removed from the retained
unique-candidate list. Unreviewed unique candidates keep their existing honest
source-labelled audit-supported status.

Final evidence outputs:

- `docs/v2_svrdd_repaired_road_unique_keep_manifest.csv`
- `docs/v2_svrdd_repaired_road_unique_quality_exclusions.csv`

## Command

```powershell
.\.venv\Scripts\python.exe src\prepare_v2_repaired_road_unique_review.py `
  --repository-root . `
  --materialized-manifest docs\v2_svrdd_repaired_road_materialization_manifest.csv `
  --unique-output docs\v2_svrdd_repaired_road_unique_manifest.csv `
  --duplicates-output docs\v2_svrdd_repaired_road_duplicate_exclusions.csv `
  --review-output docs\v2_svrdd_repaired_road_unique_quality_review_manifest.csv `
  --preview-dir data\processed\v2\svrdd\repaired_road_unique_quality_review\previews `
  --seed 42 `
  --per-region-size 4
```

## Current boundary

- Raw and processed images remain outside Git.
- Original source-image IDs and split-group IDs remain attached to every record.
- The protected V1 test set is not used.
- The completed review decisions are stored in
  `docs/v2_svrdd_repaired_road_unique_quality_review_manifest.csv`.
- No final V2 train/validation/test split exists yet.
- No V2 model is trained in this step.

## Finalization command

```powershell
.\.venv\Scripts\python.exe src\finalize_v2_repaired_road_unique_review.py `
  --unique-manifest docs\v2_svrdd_repaired_road_unique_manifest.csv `
  --review-manifest docs\v2_svrdd_repaired_road_unique_quality_review_manifest.csv `
  --keep-output docs\v2_svrdd_repaired_road_unique_keep_manifest.csv `
  --exclude-output docs\v2_svrdd_repaired_road_unique_quality_exclusions.csv
```
