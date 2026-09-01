# V2 Road Condition Labeling Guide

## Purpose and boundary

This guide defines labels for the experimental **V2 Road Condition** work on branch `codex/road-condition-v2`.

V2 does not replace the assessed V1 model. V1 remains a binary `Normal` / `Pothole` classifier for human-review triage. Do not combine V1 and V2 labels without a documented conversion and a new data audit.

This guide supports three separate experiments:

1. **Multi-class classification**: one main road-condition label for an image.
2. **Multi-label classification**: more than one visible condition can be present in an image.
3. **Object detection**: mark the location of each visible condition with a bounding box.

No model may be trained until the collected V2 data has been audited, deduplicated, and split into train, validation, and protected test sets.

## Image-level road-condition definitions

| Label | Definition | Include | Exclude |
| --- | --- | --- | --- |
| `Normal_asphalt` | An intact, paved asphalt road surface with no visible road condition or look-alike feature being recorded. | Clean asphalt with harmless texture variation. | Any visible pothole, crack, repaired patch, unpaved surface, shadow, puddle, manhole, road marking, or road stain. |
| `Pothole` | A visible hole, depression, or missing asphalt in the drivable surface. | Open holes and clearly sunken/missing pavement. | Flat dark stains, shadows, manholes, puddles, and flat repairs. |
| `Crack` | A visible fracture in paved asphalt that is not a pothole. | Linear, branching, or network cracking with no clear hole/depression. | Seams, lane markings, dirt marks, or a crack that has formed a visible pothole. |
| `Repaired_road` | A visibly repaired, filled, or patched asphalt area that is currently flat. | Filled former potholes and asphalt repair patches. | An active pothole inside a repair area; use `Pothole` for the primary multi-class label. |
| `Unpaved_road` | A road whose main visible drivable surface is soil, gravel, sand, or stones rather than asphalt. | Clearly non-asphalt road surfaces. | Asphalt with only a small dirty, gravelly, or dusty region. |
| `Shadow` | A visible shadow cast onto the road by a tree, vehicle, building, or other object. | A dark region whose shape and lighting show it is cast onto the surface. | A visible hole or depression; label that as `Pothole` even if it is partly shadowed. |
| `Puddle` | Water lying on the road surface without clear evidence of a pothole. | Reflective or wet water regions. | A clearly visible pothole containing water; label the road condition as `Pothole` and record the puddle tag too. |
| `Manhole` | A manufactured manhole, drain cover, or similar road fixture. | Circular, rectangular, or patterned utility covers. | An irregular damaged hole in the road surface. |
| `Road_marking` | A painted lane line, symbol, arrow, or other intentional road marking. | Paint with a regular, intentional shape. | Cracks, missing asphalt, or accidental stains. |
| `Road_stain` | A flat dark stain, oil mark, tire mark, or dirt patch on the road. | Flat discoloration with no visible hole/depression. | Shadows, puddles, markings, or physical road damage. |
| `Unclear_exclude` | An image that cannot be labeled honestly from visible evidence. | Severe blur, darkness, obstruction, extreme distance, or an ambiguous road surface. | Do not use as a model output class or as training data. Keep it in the issue log. |

## General rules for every labeler

1. Label what is clearly visible, not what might be hidden under a shadow, puddle, or vehicle.
2. Use the original image quality. Do not sharpen, crop, or edit an image to make a decision.
3. If evidence is insufficient, use `Unclear_exclude` and record the reason.
4. Label shadows, puddles, manholes, road markings, and road stains explicitly when visible; never label them as potholes without a visible hole or depression.
5. Preserve source information, image identifier, license, and labeler decision for every V2 image.
6. Do not include images containing identifiable people, vehicle plates, addresses, or private information unless their use and publication are permitted and documented.

## Multi-class classification policy

Multi-class classification returns exactly one main label per image. Use this priority order only when more than one condition is visible:

1. `Pothole`
2. `Crack`
3. `Repaired_road`
4. `Unpaved_road`
5. `Shadow`
6. `Puddle`
7. `Manhole`
8. `Road_marking`
9. `Road_stain`
10. `Normal_asphalt`

`Unclear_exclude` is not a training class.

Examples:

- A repaired patch containing a new hole: `Pothole`.
- A paved road with cracks but no hole: `Crack`.
- A smooth repair patch without an active pothole: `Repaired_road`.
- A clear intact asphalt road with a visible tree shadow: `Shadow`.
- A clear intact asphalt road with no look-alike feature: `Normal_asphalt`.

## Multi-label classification policy

Multi-label classification records each visible condition independently. The labels are:

- `pothole_present`: Yes/No
- `crack_present`: Yes/No
- `repaired_patch_present`: Yes/No
- `unpaved_surface_present`: Yes/No
- `shadow_present`: Yes/No
- `puddle_present`: Yes/No
- `manhole_present`: Yes/No
- `road_marking_present`: Yes/No
- `road_stain_present`: Yes/No

`Normal_asphalt` is derived only when all nine labels are `No` and the image is not excluded. An image may therefore be both `pothole_present=Yes` and `shadow_present=Yes`.

## Object-detection annotation policy

Object detection requires a bounding box for every visible target instance. It does not use `Normal_asphalt` as an object class: a normal image is a negative image with no boxes.

| Object class | Box rule |
| --- | --- |
| `pothole` | Draw one tight box around each separate visible hole or depression. Do not draw a box around only its shadow. |
| `crack` | Draw a box around a clearly visible connected crack system. A bounding box is only an approximation for thin cracks; segmentation may be a later improvement. |
| `repaired_patch` | Draw a box around the visible repaired/filled asphalt area. If it contains an active pothole, annotate both objects. |
| `unpaved_surface` | Draw a box around the visible non-asphalt road area when it can be separated clearly from the scene. |
| `shadow_region` | Draw a box around the clearly visible shadow region only when it is a useful pothole look-alike. |
| `puddle` | Draw a box around the visible water region. If a pothole is visible under the water, annotate the pothole separately too. |
| `manhole` | Draw a box around the manufactured road cover or drain. |
| `road_marking` | Draw a box around a distinct marking only when it could reasonably be confused with damage. |
| `road_stain` | Draw a box around a distinct flat stain only when it could reasonably be confused with damage. |

For detection, annotate all visible applicable objects; do not use the multi-class priority order. Overlapping boxes are allowed when a pothole occurs within a repaired patch.

## Required review before training

Before any V2 training run:

1. Review a sample from every label for correct use of this guide.
2. Record disagreements and resolve the label definition before continuing.
3. Audit for unreadable images, duplicates, source overlap, and class counts.
4. Split data by source, location, or recording session where possible, so highly similar images do not leak between train, validation, and protected test sets.
5. Freeze the protected test set before model selection.

## Current limitations

This guide creates consistent labels; it does not guarantee that a small or biased dataset will generalize. V2 must be evaluated separately on varied, properly licensed data. It must retain human review and must not make road-safety, severity, repair-cost, or repair-priority decisions.
