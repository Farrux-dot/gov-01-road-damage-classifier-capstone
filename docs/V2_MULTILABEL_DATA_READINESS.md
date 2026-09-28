# V2 Multi-Label Data Readiness Decision

## Purpose

This document starts the V2 multi-label phase after the V2 multi-class phase
was closed with one protected-test evaluation. It records the safe initial
scope before any multi-label manifest is built, images are materialized, or a
multi-label model is trained.

Multi-label classification answers a different question from multi-class
classification: an image may receive every road-condition label that is
verified as present. For example, one image may be labelled both `crack` and
`pothole`.

## Decision

The first multi-label dataset must use only the **6,000 SVRDD source training
records** represented in `docs/v2_candidate_inventory.csv`.

Its initial label set is deliberately limited to the four conditions for which
SVRDD provides complete source annotations:

1. `crack`
2. `pothole`
3. `repaired_road`
4. `manhole_cover`

This is an image-level multi-label task derived from the already converted
SVRDD boxes. A label is `1` when at least one corresponding source box exists
in the image, and `0` when that condition has no source box in that image.

## Verified evidence

The candidate inventory contains 14,865 source-traceable candidates. Of those,
12,382 have at least one recorded multi-label and 2,215 contain more than one
condition. All 2,215 currently recorded mixed-condition examples are from
SVRDD.

For the selected SVRDD core:

| Check | Verified result |
| --- | ---: |
| Eligible source records | 6,000 |
| Original source split used | `train` only |
| Recorded mixed-condition images | 2,215 |
| `crack` positive images | 4,253 |
| `repaired_road` positive images | 2,077 |
| `manhole_cover` positive images | 1,688 |
| `pothole` positive images | 472 |

The source conversion record in `docs/V2_SVRDD_CONVERSION.md` verifies that
the four source categories were converted without dropping any of the 20,804
source objects. It also explicitly confirms that SVRDD does not provide the
other planned V2 multi-label conditions.

Examples of already verified label combinations include:

- `crack;manhole_cover` — 1,151 images
- `crack;repaired_road` — 299 images
- `pothole;crack` — 201 images
- `pothole;crack;manhole_cover` — 133 images
- `pothole;manhole_cover;repaired_road` — 11 images
- all four conditions — 4 images

## Why the initial scope is limited

The repository includes other sources with a confirmed single positive label,
such as road markings, speed bumps, or image-level potholes. Those sources do
not yet verify every other multi-label condition as absent. Treating an
unrecorded condition as `0` would create false negative labels.

Therefore, the following active project conditions are **not** included in the
first core multi-label dataset until a separate machine-readable source audit
has verified their coverage:

- `unpaved_road`
- `speed_bump`
- `road_marking`

The following conditions are explicitly excluded from the active project scope
and must not be researched, added, materialized, or trained in this phase:

- `shadow`
- `puddle`
- `road_stain`

`normal_asphalt` is not a direct multi-label class in this scope. It would be
an all-zero condition vector only after all relevant conditions have been
verified as absent.

## Boundaries that remain in force

- The V2 multi-class materialization and its protected test are closed. They
  must not be reused, relabelled, or evaluated as a multi-label test set.
- The V2-E2 label-quality review remains useful evidence of real co-occurring
  conditions, but it does not automatically alter any label.
- Do not mix partially annotated sources into ordinary binary cross-entropy
  training as though every missing label means "not present".
- Do not materialize images, create splits, or train a model until the
  multi-label candidate manifest and its split/leakage audit are reviewed.

## Automation-only labeling policy

No student image-by-image review is required for this phase.

The four-label vectors will be generated automatically from SVRDD's existing
machine-readable source boxes. For each image, the manifest builder will mark
a condition as `1` if its converted source annotation contains one or more
boxes for that condition, otherwise `0`. It will preserve the original source
image and annotation paths as evidence.

The required quality checks will also be automated:

- source image and annotation path existence;
- annotation parsing and valid box-label mapping;
- agreement between object labels and the derived four-label vector;
- image readability;
- exact-duplicate and near-duplicate checks across proposed splits;
- per-label and per-combination split counts.

The three active conditions that lack complete source annotation coverage will
remain outside this first model until an additional source audit is complete.
They will not be guessed, pseudo-labelled, or marked absent automatically. A
future expansion may use another source with complete machine-readable
annotations, or a mask-aware learning design that preserves unknown labels
rather than turning them into false negatives.

## Speed-bump strengthening update

The speed-bump class must not rely on RTK alone: RTK contributes only eight
speed-bump-positive images. The project has two larger, already audited
image-level speed-bump sources:

| Source | Confirmed, conflict-safe speed-bump-positive images |
| --- | ---: |
| Kaggle Speed Bump Dataset | 1,076 |
| Mendeley Manhole / Speed-Breaker Dataset | 147 |
| RTK semantic-segmentation source | 8 |
| Total available speed-bump-positive evidence | 1,231 |

The Kaggle records are the previously audited, exact-unique, non-sequence
source-`train` candidates. The Mendeley records exclude the three known
cross-label conflict cases. These images confirm that a speed bump is present,
but do not label the other active conditions. They therefore enter the
annotation-coverage manifest with `speed_bump_present = 1`; every other
condition remains unknown, not absent. This requires no student image review.

This strengthens the available evidence for speed bump without making an
unsupported claim that the other conditions are absent.

## Current non-materialized coverage manifest

The automated coverage-manifest builder now combines 7,924 source records:

- 6,000 SVRDD records with four fully known conditions;
- 701 RTK records with six fully known conditions (not manhole cover);
- 1,076 audited Kaggle speed-bump-positive records; and
- 147 conflict-safe Mendeley speed-bump-positive records.

It copies no image and creates no training split. Its generated CSV and
summary stay in ignored `reports/` storage. The reusable builder and test are
tracked source code.

## Next approved-sized task

Audit the strengthened **non-materialized annotation-coverage manifest**
before any materialization or training. This audit must verify source paths,
image readability, exact duplicates across all sources, and near-duplicate
risks before proposing any source-aware split.

Before that manifest can be materialized or used for training, verify:

1. every image has a valid four-label vector;
2. positive counts match the verified values above;
3. exact duplicates and near-duplicates do not cross proposed splits;
4. source paths exist and source annotations agree with each vector;
5. automated image-readability, label-vector, and split-coverage checks pass.
