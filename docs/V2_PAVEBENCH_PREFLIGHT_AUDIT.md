# V2 PaveBench Preflight Audit

**Audit date:** 2026-09-06  
**Scope:** downloaded PaveBench classification and object-detection tasks only  
**Raw-data location:** `data/raw/v2/pavebench/data` (Git ignored)

## Purpose

This preflight answers a narrow question: are the downloaded PaveBench files
structurally safe to consider for later V2 review? It does **not** create a
V2 split, merge PaveBench with SVRDD, train a model, or evaluate a model.

## Source record

- Source: [VVQNN/PaveBench on Hugging Face](https://huggingface.co/datasets/VVQNN/PaveBench)
- Dataset-card licence: **CC BY-NC-SA 4.0**
- Downloaded on: 2026-09-06
- Downloaded tasks: classification and object detection
- Not downloaded for this stage: segmentation and VQA task copies

The licence is non-commercial and share-alike. It must remain recorded if any
PaveBench material is used in V2.

## Detection structure checks

The audit opened every downloaded detection JPEG, compared it with its COCO
record, and checked every COCO bounding box against the real image dimensions.

| Source split | COCO image records | JPEG files | Boxes | Missing or extra files | Unreadable images | Dimension mismatches | Invalid boxes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| train | 9,518 | 9,518 | 9,518 | 0 | 0 | 0 | 0 |
| val | 1,177 | 1,177 | 1,177 | 0 | 0 | 0 | 0 |
| test | 1,162 | 1,162 | 1,162 | 0 | 0 | 0 | 0 |
| **Total** | **11,857** | **11,857** | **11,857** | **0** | **0** | **0** | **0** |

The supplied detection JSON uses exactly these four categories:

| PaveBench detection label | Boxes | Honest V2 position |
| --- | ---: | --- |
| `alligator` | 2,091 | Candidate for `Crack` after later mapping review |
| `crack` | 6,896 | Candidate for `Crack` after later mapping review |
| `patch` | 2,557 | Candidate for `Repaired_road` only after visual review |
| `pothole` | 313 | Candidate for `Pothole` after later source-combination review |

## Classification source labels

The classification folders contain 20,124 JPEG files:

| Source label | Images | Meaning for V2 |
| --- | ---: | --- |
| `alligator_crack` | 2,091 | Candidate crack image class |
| `longitudinal_crack` | 3,832 | Candidate crack image class |
| `transverse_crack` | 3,064 | Candidate crack image class |
| `patch` | 2,557 | Candidate repaired-road class after visual review |
| `pothole` | 313 | Candidate pothole image class |
| `negative` | 8,267 | Generic candidate pool only; not a named V2 look-alike label |

`negative` must **not** be automatically relabelled as `Shadow`, `Puddle`,
`Road_stain`, `Road_marking`, `Normal_asphalt`, or `Unpaved_road`. Those
conditions require explicit human labels.

## Important duplicate risk

The audit found **22 exact duplicate image groups across PaveBench's supplied
detection train, validation, and test folders**. This creates leakage if those
source-provided splits are used directly.

**Decision:** PaveBench is structurally usable as a candidate source, but its
provided splits are **not accepted** as V2 training, validation, or protected
test splits. Before use, selected PaveBench images must be deduplicated and
split again alongside any other V2 sources.

## What this audit does not prove

- It does not prove that `patch` always means a repaired road in our V2 task.
- It does not label shadows, puddles, stains, road markings, clear asphalt, or
  unpaved road.
- It does not prove generalisation, model accuracy, or readiness for training.
- It does not remove duplicates or build any V2 split.

## Reproducibility

Run from the repository root after the raw PaveBench classification and
detection data are available:

```powershell
.\.venv\Scripts\python.exe src\audit_pavebench.py `
  --data-dir data\raw\v2\pavebench\data `
  --output reports\v2_pavebench_audit.json
```

The generated JSON report is ignored by Git because it is reproducible from
the raw data. The tracked source code and this document record the audit logic
and conclusions.
