# V2 Road-Shadow Finder: Preflight Experiment

## Purpose

This is a small preparation experiment. Its future job is to help find likely
road-shadow images in the local StreetSurfaceVis source for human review. It
is **not** the final GOV-01 model and it must not replace V1.

## Approved inputs

| Source | Approved images | Extra information | Current role |
| --- | ---: | --- | --- |
| SRD road-shadow sample | 24 | Each image has a shadow mask | Experimental shadow-pattern evidence only |
| ISTD shadow sample | 20 | Each image has a shadow mask | Experimental shadow-pattern evidence only; research/non-commercial condition recorded |
| StreetSurfaceVis | 59 | Real-road images, manually approved; no masks | Road-context confirmation and later candidate-mining check |
| **Total** | **103** | Not a final training split | Preparation only |

Seven other approved StreetSurfaceVis shadow images are intentionally absent:
they belong to the source's official non-training split and remain protected.

## Label meaning

For every approved StreetSurfaceVis image:

- main road label: `normal_asphalt`
- extra condition: `shadow`

This means “normal asphalt with a shadow,” not “pothole.” The `shadow` label
is stored in `docs/v2_shadow_multilabel_manifest.csv` and does not create a
duplicate image record.

## Required check

Run this from the repository root:

```powershell
.\.venv\Scripts\python.exe src\preflight_shadow_finder.py
```

The check confirms files and masks are readable, confirms all 59 road-shadow
overlays refer to existing `normal_asphalt` source-training candidates, and
reports the current blocker.

## Boundary before any model experiment

No model training is approved yet because the V2 final split does not exist.
Also, SRD provenance/license and ISTD's stated research/non-commercial condition
must be confirmed for the intended use. When those conditions are resolved, a
candidate-mining experiment may rank unreviewed StreetSurfaceVis images by
likely shadow presence. The ranking is only a shortlist: the student must
review and approve or reject every proposed new shadow label.
