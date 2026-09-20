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

## Proposed safe split method — not executed yet

When the V2 multi-class experiment is explicitly approved, construct one
deterministic split from the 12,768 multi-class candidates:

| Split | Proposed share | Purpose |
| --- | ---: | --- |
| Training | 70% | Learn model parameters and use augmentation only here |
| Validation | 15% | Compare model approaches and choose settings |
| Protected test | 15% | One final evaluation after model selection |

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

## Next small approved task

Create a deterministic, source-aware V2 **split manifest generator** and its
automated checks. It should only write a CSV manifest first; it must not copy
images or train a model. The checks must prove that every candidate is assigned
once, labels are represented where possible, and no exact duplicate or source
image group crosses split boundaries.
