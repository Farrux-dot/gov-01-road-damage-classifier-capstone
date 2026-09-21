# V2 Multi-Class Data Gate Decision

**Decision date:** 2026-09-21  
**Scope:** The proposed V2 multi-class image-classification split only. This
does not approve object detection, multi-label training, materialization, or
model training.

## Decision

**PASS — approved for a separately approved V2 data-materialization task.**

The final manifest is safe to use as the plan for creating future
train/validation/protected-test folders. This decision does not copy, move,
delete, link, relabel, or train on any image. A separate approval is still
required before materialization, and another approval is required before any
V2 training.

## Verified gate checks

| Gate check | Verified result | Evidence |
| --- | --- | --- |
| Candidate inventory identity | 14,865 source-traceable records; no repeated candidate IDs | `reports/v2_final_candidate_audit.json` |
| Eligible classification records | 12,768 records with a non-empty proposed primary label | `docs/v2_multiclass_split_manifest_near_duplicate_final.csv` |
| Source-file presence | 0 missing referenced source files | `reports/v2_final_candidate_audit.json` |
| Active-image readability | 12,764 active image files decode successfully; 0 unreadable | Read-only Pillow verification on 2026-09-21 |
| Exact duplicate content | 0 stored SHA-256 duplicate groups in the candidate inventory | `reports/v2_final_candidate_audit.json` |
| Source split leakage | 0 source validation/test records included | `reports/v2_final_candidate_audit.json` |
| Final-manifest structure | 12,768 unique candidate IDs; 0 split groups cross a split boundary | Final-manifest verification on 2026-09-21 |
| Near-duplicate leakage | 911 reviewed pairs; 0 pairs cross a final split boundary | `docs/v2_cross_split_near_duplicate_pairs_reviewed.csv` |
| Remaining visual review | 0 pending pairs | `docs/v2_cross_split_near_duplicate_review_queue_final.csv` |
| Label conflicts | Two conflicting duplicate families; four records excluded, not guessed or relabeled | `docs/V2_FINAL_DATA_AUDIT_AND_SPLIT_PLAN.md` |

## Final metadata split

| Assignment | Records |
| --- | ---: |
| Training | 9,452 |
| Validation | 1,658 |
| Protected test | 1,654 |
| Excluded label conflict | 4 |
| Total candidate records | 12,768 |

The four excluded records are intentionally outside every future split. The
12,764 active records have a proposed image-level primary label. They are not
object-detection annotations and must not be represented as detection-ready
data.

## Boundaries that remain in force

- The final CSV is metadata only. There are no final V2 image folders yet.
- Raw data remains unchanged and out of Git.
- The protected test must not be used for augmentation, balancing, model
  selection, or tuning.
- V1 remains the frozen assessed binary project; V2 does not replace it.
- This gate verifies the documented candidate labels and their split safety. It
  does not claim that every image-level source label is semantically perfect.

## Next permitted task

With separate approval, materialize only the 12,764 active records from
`docs/v2_multiclass_split_manifest_near_duplicate_final.csv` into new V2
train/validation/protected-test folders. The operation must preserve raw data,
verify copied or linked file hashes, and produce a materialization report.
