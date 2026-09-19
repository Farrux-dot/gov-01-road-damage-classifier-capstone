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
| StreetSurfaceVis | 155 | Real-road images, manually approved; no masks | Road-context confirmation and later candidate-mining check |
| StreetSurfaceVis clear no-shadow review | 51 | Real-road images, manually approved; no masks | Small trusted no-shadow comparison set |
| **Shadow-positive total** | **199** | Not a final training split | Preparation only |

Seven other approved StreetSurfaceVis shadow images are intentionally absent:
they belong to the source's official non-training split and remain protected.

## Label meaning

For every approved StreetSurfaceVis image:

- main road label: `normal_asphalt` or `unpaved_road`
- extra condition: `shadow`

This means “normal asphalt with a shadow,” not “pothole.” The `shadow` label
is stored in `docs/v2_shadow_multilabel_manifest.csv` and does not create a
duplicate image record.

The completed no-shadow review kept 51 different StreetSurfaceVis source-training
images. They remain `normal_asphalt` records and are listed separately in
`docs/v2_no_shadow_manifest.csv` with the verified condition
`no_visible_road_shadow`. This is a reviewed absence condition, not a new model
output label. Nine reviewed images with a visible shadow were excluded from the
no-shadow set and recorded in `docs/v2_streetsurfacevis_no_shadow_review_decisions.csv`.

## Required check

Run this from the repository root:

```powershell
.\.venv\Scripts\python.exe src\preflight_shadow_finder.py
```

The check confirms files and masks are readable, confirms all 155 road-shadow
overlays and all 51 clear no-shadow records refer to existing eligible
source-training road candidates, confirms the two sets do not overlap, and
reports the current blocker.

## Boundary before any model experiment

No model training is approved yet because the V2 final split does not exist.
Also, SRD provenance/license and ISTD's stated research/non-commercial condition
must be confirmed for the intended use. When those conditions are resolved, a
candidate-mining experiment may rank unreviewed StreetSurfaceVis images by
likely shadow presence. The ranking is only a shortlist: the student must
review and approve or reject every proposed new shadow label.

## Review-only StreetSurfaceVis scan

`src/prepare_v2_streetsurfacevis_shadow_candidates.py` implements that safe
first shortlist step. It scans only the remaining eligible StreetSurfaceVis
source-training road images and skips all records already shown in the shadow
or no-shadow reviews. It uses a simple local-dark-region heuristic; it does
not learn from SRD/ISTD, create training labels, or change the final inventory.

A dark area may be a shadow, dark asphalt, a puddle, a stain, or camera
exposure. Each new candidate therefore remains `pending` until human review.

## Completed heuristic-candidate review

The completed 120-image human review retained **96** images with a visible
road shadow and excluded **24** images where no road shadow was visible. The
approved images remain existing StreetSurfaceVis source-training records; they
receive a `shadow` multi-label overlay in
`docs/v2_shadow_multilabel_manifest.csv` and do not create duplicate image
records. No final split or V2 model training was created.
