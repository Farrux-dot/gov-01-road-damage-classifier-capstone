# V2 N-RDD2024 Data Audit

## Decision

**Approved as a derived source for four conditions only:** `crack`,
`pothole`, `repaired_road`, and `manhole_cover`. It has been added only to a
new, separately materialized V2 expansion split. No model was trained from
that split.

## Source and boundary

- Official source: <https://data.mendeley.com/datasets/27c8pwsd6v/5>
- Version: 5, published 20 November 2024.
- Licence stated on the source page: CC BY 4.0.
- Only the eight official **Training and Validation Dataset** VOC archives
  were used for the audit. The official source test images were not extracted,
  inspected, or used.

## Complete structural audit

| Check | Result |
| --- | ---: |
| Outer archive full-content read | Passed |
| Inner VOC archives fully read | 8 of 8 passed |
| Training/validation images | 23,433 |
| XML annotations | 23,433 |
| Unreadable images | 0 |
| Images missing XML | 0 |
| XML files missing an image | 0 |
| Exact duplicates inside N-RDD2024 | 0 |
| Exact duplicates against current V2 multi-label data | 0 of 23,433 |

## Label mapping

| N-RDD2024 label | Project condition | Decision |
| --- | --- | --- |
| D00, D10, D20 | `crack` | Included |
| D40 | `pothole` | Included |
| D30 repaired crack | `repaired_road` | Included |
| D70 | `manhole_cover` | Included |
| D80 patchy road | — | Excluded: it is not automatically assumed to be a repaired road |
| D50, D60, D90 | — | Outside the active project conditions |

The derived manifest marks only the four included conditions as known. For
`unpaved_road`, `road_marking`, and `speed_bump`, values remain unknown rather
than being incorrectly changed into negative labels.

## Boundary-box correction

The audit found 1,729 source boxes with an endpoint past the image boundary.
Every affected box was safe to correct:

| Overflow pattern | Boxes |
| --- | ---: |
| Right edge one pixel past (`xmax + 1`) | 885 |
| Bottom edge one pixel past (`ymax + 1`) | 806 |
| Both edges one pixel past | 38 |

No larger overflow, inverted box, missing coordinate, or malformed XML was
found. The derived manifest clips only `xmax` and/or `ymax` to the image
boundary. It does not alter the raw XML files, images, or class labels.

For the four mapped project conditions, 1,344 box endpoints were clipped. The
remaining corrected boxes belong to source labels outside this project scope.

## Derived candidate output

Run:

```powershell
.venv\Scripts\python.exe src\build_n_rdd2024_multilabel_candidate.py `
  --source-root data\raw\n_rdd2024\fresh_voc_extracted `
  --manifest data\processed\n_rdd2024_multilabel_candidate\n_rdd2024_multilabel_candidate.jsonl `
  --report data\processed\n_rdd2024_multilabel_candidate\n_rdd2024_clipping_report.json
```

The generated manifest contains 23,433 records. Its validated positive-image
counts are 18,717 for `crack`, 2,378 for `pothole`, 2,498 for
`repaired_road`, and 2,830 for `manhole_cover`.

## Remaining boundary

The source is now part of a separately audited V2 expansion split. It does not
alter the earlier multi-label dataset, its models, its results, or its already
used test set. The new expansion has a fresh test split that must remain
unseen until a new model candidate is locked.

See [`V2_N_RDD2024_EXPANSION_SPLIT_AUDIT.md`](V2_N_RDD2024_EXPANSION_SPLIT_AUDIT.md)
for the combined-pool audit and materialization result.
