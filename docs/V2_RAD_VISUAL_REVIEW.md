# RAD Unsurfaced-Road Visual Review

**Review date:** 2026-09-11  
**Source:** RAD Road Anomaly Detection version 3  
**Proposed V2 mapping:** source `UnsurfacedRoad` to V2 `Unpaved_road`  
**Decision:** rejected for the current V2 label

## Review evidence

The workbook contains 60 deterministic source-training examples selected with
seed `42`. The recorded choices are:

| Workbook choice | Count |
| --- | ---: |
| `clear_unpaved_keep` | 33 |
| `not_unpaved_exclude` | 26 |
| `pending` | 1 |
| **Total** | **60** |

These choices are preserved as review history, but the 33 preliminary keep
choices are not accepted into the V2 inventory because the review rule was too
broad. It asked whether any unsurfaced road area was visible rather than
whether the main drivable road surface was unpaved.

## Confirmed semantic mismatch

The reviewer reported that most scenes show asphalt coverage. Direct inspection
confirmed that some `UnsurfacedRoad` boxes describe a small dirt shoulder or
road-edge region while the main road remains asphalt. For example,
`RAD-UNPAVED-033` was preliminarily marked keep, but its class-5 box is at the
bottom-left road edge and the main driving lane is asphalt.

This source meaning does not match the current V2 definition of
`Unpaved_road`: the main drivable road surface must be visibly unpaved. Using
these images would teach the model that asphalt roads with dirt shoulders are
unpaved roads.

## Repeated-scene evidence

The 60 files contain no byte-for-byte exact duplicate. They do contain many
frames from the same source videos:

- 60 review rows come from 38 recording groups;
- 16 recording groups appear more than once;
- one recording group contributes five rows;
- a 64-bit difference-hash check found 8 highly similar same-recording pairs
  at Hamming distance 12 or lower.

The highly similar pairs are:

- `RAD-UNPAVED-009` and `RAD-UNPAVED-045`
- `RAD-UNPAVED-024` and `RAD-UNPAVED-040`
- `RAD-UNPAVED-033` and `RAD-UNPAVED-053`
- `RAD-UNPAVED-020` and `RAD-UNPAVED-058`
- `RAD-UNPAVED-006` and `RAD-UNPAVED-042`
- `RAD-UNPAVED-041` and `RAD-UNPAVED-048`
- `RAD-UNPAVED-028` and `RAD-UNPAVED-051`
- `RAD-UNPAVED-042` and `RAD-UNPAVED-052`

These are near-duplicate video frames, not exact file duplicates. They reduce
visual variety and must be grouped together if the source is ever used for a
different task.

## Data Gate decision

RAD version 3 is rejected as the current V2 `Unpaved_road` source. No reviewed
RAD row is accepted into the candidate inventory. The remaining 479
source-labelled images will not be reviewed because the source label does not
match the project label closely enough.

The raw RAD files remain Git-ignored and unchanged. No final split was created
and no model was trained or evaluated with RAD.

## Next action

Find a source where the image-level meaning is explicitly that the main road
surface is unpaved, or collect permission-based examples and label them with
the stricter rule. Sampling must use one representative per recording group
before any extra frames are considered.
