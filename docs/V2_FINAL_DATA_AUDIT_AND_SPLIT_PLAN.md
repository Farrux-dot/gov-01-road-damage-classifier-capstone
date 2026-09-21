# V2 Final Candidate Data Audit and Split Plan

**Audit date:** 2026-09-20  
**Scope:** V2 candidate inventory only. No V2 model was trained and no final
train/validation/test folders were created by this audit.

## What was checked

The reproducible audit reads `docs/v2_candidate_inventory.csv` and checks the
currently approved candidate records before any final split is made.

| Check | Result |
| --- | ---: |
| Candidate image records | 14,865 |
| Candidate IDs repeated | 0 |
| Missing referenced source images | 0 |
| Empty stored SHA-256 hashes | 0 |
| Exact duplicate SHA-256 groups | 0 |
| Source validation/test records accidentally included | 0 |
| Multi-class split candidates | 12,768 |
| Records without a proposed multi-class label | 2,097 |

The full machine-readable result is in
`reports/v2_final_candidate_audit.json`.

## Current multi-class candidate coverage

These are full-image candidates with one proposed primary label. They are not
yet a final train/validation/test split.

| Proposed output label | Candidate images | Main sources |
| --- | ---: | --- |
| `crack` | 3,907 | SVRDD |
| `pothole` | 2,337 | SVRDD, V1 training-only data, approved GitHub source |
| `repaired_road` | 1,620 | SVRDD |
| `normal_asphalt` | 1,390 | StreetSurfaceVis, student-filtered Zenodo normal images |
| `speed_bump` | 1,223 | Kaggle Speed Bump, student-approved Mendeley data |
| `manhole_cover` | 1,198 | Hugging Face manhole covers, one SVRDD primary-label record |
| `unpaved_road` | 1,093 | StreetSurfaceVis, student-filtered RQD class 5 |

The 2,097 CeyMo records remain outside the multi-class pool because they prove
road-marking presence but do not prove that all other V2 conditions are absent.
They may later support a separate multi-label or detection experiment only.

## Important boundaries

- V1 remains the assessed binary project. V2 is a separate experiment and must
  not replace V1 without its own completed evidence.
- V1 validation/protected-test images and SVRDD validation/test images are not
  included here.
- Image-level labels without boxes cannot be used to train object detection.
- A high total count does not guarantee equal visual variety across sources.
- Stored SHA-256 checks find byte-identical files. They do not prove that
  visually similar photographs are different.

## Generated safe split manifest — not materialized

The deterministic split manifest was generated from the 12,768 eligible
multi-class candidates using seed `42`. It exists only as metadata in
`docs/v2_multiclass_split_manifest.csv`; no images were copied and no model was
trained.

| Split | Proposed share | Purpose |
| --- | ---: | --- |
| Training | 8,936 (70.0%) | Learn model parameters and use augmentation only here |
| Validation | 1,916 (15.0%) | Compare model approaches and choose settings |
| Protected test | 1,916 (15.0%) | One final evaluation after model selection |

| Primary label | Training | Validation | Protected test |
| --- | ---: | ---: | ---: |
| `crack` | 2,735 | 586 | 586 |
| `manhole_cover` | 838 | 180 | 180 |
| `normal_asphalt` | 972 | 209 | 209 |
| `pothole` | 1,635 | 351 | 351 |
| `repaired_road` | 1,134 | 243 | 243 |
| `speed_bump` | 857 | 183 | 183 |
| `unpaved_road` | 765 | 164 | 164 |

The generator checks that every candidate appears once and that each original
source-image group stays entirely in one split. The generated manifest has
12,768 unique candidate IDs and 12,768 split groups; zero groups cross a split
boundary. Its machine-readable summary is
`reports/v2_multiclass_split_report.json`.

Before assigning a split, the split builder must:

1. Use only rows with a non-empty `proposed_multiclass_label`.
2. Keep every exact-hash group together. The current audit found no repeated
   groups, but the guard remains necessary.
3. Keep related records from the same original source image together if crops
   or multiple derived records are added later.
4. Perform a near-duplicate review before splitting. Similar-looking images
   must not silently land in both training and protected test sets.
5. Stratify by primary label **and source**, as far as each source has enough
   images. This avoids putting nearly all examples from one source into only
   one split.
6. Use one fixed recorded random seed so the split can be rebuilt exactly.
7. Write a split manifest containing candidate ID, source ID, original source
   record ID, SHA-256, primary label, split name, and split-group ID.
8. Copy or link images only after the manifest passes its checks. Raw datasets
   remain unchanged and out of Git.

The test split must stay untouched while models are trained and tuned. It is
not a source for augmentation, class balancing, threshold selection, or model
comparison.

## Cross-split near-duplicate audit — completed

The split manifest was scanned with a conservative visual shortlist: a compact
grayscale difference hash, matched brightness/contrast bins, and a small
thumbnail comparison. This finds possible visual duplicates, including
re-encoded copies that do not have the same SHA-256 file hash. It does **not**
delete, relabel, move, or copy any images.

| Check | Result |
| --- | ---: |
| Manifest images scanned | 12,768 |
| Cross-split suspicious pairs | 911 |
| Unique images involved in one or more pair | 1,088 |
| Same visual hash (distance 0) pairs | 293 |
| Pairs requiring a single-split holdout policy (distance 0–3) | 824 |
| Same-label pairs | 909 |
| Different-label pairs requiring label-conflict inspection | 2 |

The largest concentrations are 1,208 speed-bump pairs inside the Kaggle Speed
Bump source, 491 pairs inside SVRDD, and 315 pothole pairs shared by the V1
training-only source and the approved GitHub pothole source. The machine
readable shortlist is `docs/v2_cross_split_near_duplicate_pairs.csv`; the
reproducible summary is `reports/v2_cross_split_near_duplicate_audit.json`.

## Resolution status and remaining blocker

All 911 shortlisted pairs were reviewed. They form 375 confirmed exact-
duplicate families containing 1,088 records. The metadata-only resolution
manifest keeps each same-label family in training, so none of its members
remains in validation or the protected test. This conservative choice avoids
evaluating on a visual copy while preserving raw data and never copying,
deleting, or relabelling an image.

- Reviewed pairs:
  `docs/v2_cross_split_near_duplicate_review_manifest.csv`
- Final manifest:
  `docs/v2_multiclass_split_manifest_near_duplicate_final.csv`
- Reproducible resolver:
  `src/resolve_v2_near_duplicate_families.py`

Two confirmed duplicate families have conflicting labels: one `pothole` /
`crack` family and one `crack` / `repaired_road` family. Their four records are
excluded from every split rather than forcing a label decision. The final
metadata plan contains 9,452 training, 1,658 validation, 1,654 protected-test,
and four excluded label-conflict records.

The near-duplicate gate is now complete. The plan remains metadata-only: do
not copy or link image files until a separate, approved materialization task.
No V2 model may be trained before the Data Gate is documented as complete, and
the protected test must remain untouched during model selection.
