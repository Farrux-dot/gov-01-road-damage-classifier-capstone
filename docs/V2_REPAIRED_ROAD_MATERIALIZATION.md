# V2 SVRDD Repaired-Road Crop Materialization

## Purpose

This step converts the 2,676 retained repaired-road candidate records into actual image crops for later classification experiments. It uses only SVRDD source-training images and the audited keep manifest.

This step does not create a final train/validation/test split and does not train or evaluate a model.

## Crop rule

- Each output is a square crop centred on one repaired-road box.
- The square side is 2.5 times the longer side of the target box, with a minimum of 128 pixels.
- The crop is moved when necessary so it remains inside the original image.
- The crop is not enlarged or resized during materialization.
- Images are saved as RGB JPEG files at quality 95.
- Filenames are derived from a SHA-256 hash of the stable candidate ID, making them safe on Windows and repeatable.

The same contextual crop geometry was used by the repaired-road audit. Keeping road context helps the classifier see both the repaired patch and the surrounding road surface.

## Actual materialization result

| Check | Result |
|---|---:|
| Retained manifest rows | 2,676 |
| JPEG crops created | 2,676 |
| Unique candidate IDs | 2,676 |
| Unique source images | 1,513 |
| Unique split groups | 1,513 |
| Individually human-approved crops | 91 |
| Source-labelled, audit-supported crops | 2,585 |
| Smallest crop side | 128 px |
| Largest crop side | 1,024 px |
| Materialized folder size | 230.37 MB |

Every crop retains `split_group_id = svrdd::train::<source_image_id>`. Therefore, all crops taken from one original road image can be kept in the same future split.

## Exact-duplicate check

SHA-256 comparison found 23 exact-duplicate crop groups containing 24 redundant crops beyond the first copy.

- All 23 duplicate groups occur within the same original source image.
- Zero duplicate groups cross source-image IDs.
- Zero duplicate groups cross split-group IDs.

This means the duplicates do not currently create cross-group leakage. However, repeated identical crops could give those road scenes extra influence during training. A later deduplication step should retain one crop per exact hash for classification while keeping the original object annotations available for object-detection work.

If one crop per exact hash is retained, the provisional unique-content count is 2,652. That number is not yet a final split count.

## Outputs

- Git-ignored image directory: `data/processed/v2/svrdd/repaired_road_candidates/repaired_road/`
- Traceability manifest: `docs/v2_svrdd_repaired_road_materialization_manifest.csv`
- Reproduction tool: `src/materialize_v2_repaired_road_candidates.py`
- Automated checks: `tests/test_materialize_v2_repaired_road_candidates.py`

The image directory is intentionally ignored by Git. The CSV manifest contains portable repository-relative paths and checksums but no raw image data.

## Reproduction command

```powershell
.\.venv\Scripts\python.exe -B src\materialize_v2_repaired_road_candidates.py `
  --repository-root . `
  --keep-manifest docs\v2_svrdd_repaired_road_keep_manifest.csv `
  --output-dir data\processed\v2\svrdd\repaired_road_candidates\repaired_road `
  --output-manifest docs\v2_svrdd_repaired_road_materialization_manifest.csv
```

## Important boundaries

- These crops are candidates for image-level classification, not a finished dataset.
- Object detection must continue to use traceable object boxes from the source annotations; it must not treat a classification crop as a complete detection annotation.
- The 91% manual sample acceptance rate remains review evidence, not model accuracy.
- No protected validation or test data was used.
- No model was trained and no performance metric was generated in this step.

## Next small task

Create a deterministic classification deduplication decision that keeps one candidate per exact crop hash, then generate a targeted visual-quality sample from the remaining unique crops. Do not create the final combined V2 split until that sample is reviewed.
