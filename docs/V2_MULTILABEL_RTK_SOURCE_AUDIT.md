# V2 RTK Semantic-Segmentation Source Audit

## Purpose

This audit records an additional public source for the active V2 multi-label
conditions that are not fully represented by SVRDD. It does not materialize a
dataset, change an existing split, or train a model.

## Source and local storage

The source is the official LAPIX/UFSC RTK road-surface semantic-segmentation
ground truth. The official dataset page provides three matching archives:

- 701 original PNG frames;
- 701 numeric PNG masks; and
- 701 LabelMe-style JSON polygon annotations.

They are stored outside Git at
`data/raw/rtk_semantic_segmentation/`. The project `.gitignore` excludes
`data/raw/`, so these raw archives do not appear in GitHub Desktop.

Source page: <https://lapix.ufsc.br/pesquisas/projeto-veiculo-autonomo/datasets/?lang=en>

The source page asks users to cite the RTK semantic-segmentation work. It does
not state a separate machine-readable data licence; this must be retained as a
provenance and reuse-risk note for the final project documentation.

## Verification performed

The downloaded archives were read without extracting or altering their
contents. Each has 701 aligned records:

| Archive | Verified contents |
| --- | --- |
| `RTK_SemanticSegmentationGT_originalFrames.zip` | 701 PNG road frames |
| `RTK_SemanticSegmentationGT_NoColorMapMasks.zip` | 701 numeric PNG masks |
| `RTK_SemanticSegmentationGT_Json.zip` | 701 JSON polygon annotations |

The JSON annotations contain source labels and polygon points. They are
machine-readable source evidence, not model-generated labels and not student
reviews.

## Active-condition coverage

The counts below mean the number of RTK images that contain at least one
polygon of the named source class.

| Project condition | RTK source label | Images | Polygon shapes | Use |
| --- | --- | ---: | ---: | --- |
| `unpaved_road` | `roadUnpaved` | 270 | 289 | Supported |
| `road_marking` | `roadMarking` | 221 | 1,011 | Supported |
| `speed_bump` | `speedBump` | 8 | 8 | Supported, but too scarce to be a standalone strong class |
| `crack` | `craks` | 157 | 426 | Supported |
| `pothole` | `pothole` | 57 | 105 | Supported |
| `repaired_road` | `patchs` | 75 | 95 | Candidate mapping; preserve the source name in any manifest |

RTK does **not** annotate `manhole_cover`. Existing SVRDD annotations remain
the verified source for that condition.

The source also contains `waterPuddle`, but puddle is excluded from the active
project scope. It must not be added to a manifest or model for this phase.

## Safe integration decision

RTK expands the project with complete annotation for the RTK taxonomy, but it
does not tell us whether a manhole cover is absent in an RTK image. Conversely,
SVRDD does not annotate `unpaved_road`, `road_marking`, or `speed_bump`.

Therefore, do not merge RTK and SVRDD into an ordinary multi-label training
table that turns every unrecorded class into `0`. That would introduce false
negative labels.

The next safe technical step is an **annotation-coverage manifest**. For each
image and each active condition, it will store both:

1. whether the condition is present; and
2. whether that condition is actually known by the source.

This permits a later masked-loss training design: the model is scored only on
labels that the source really annotates. It requires no manual image review.
Before materialization or training, the manifest must be audited for paths,
source-label mapping, coverage counts, splits, and duplicate leakage.
