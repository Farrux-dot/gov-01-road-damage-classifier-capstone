# V2 SVRDD Structural Data Audit

## Scope

This audit covers the first acquired V2 source only: [SVRDD_YOLO](https://huggingface.co/datasets/ShuoZheLi/SVRDD_YOLO). The raw ZIP archives, extracted images, metadata, and JSON report remain in the ignored `data/raw/v2/svrdd/` folder and are not committed to Git.

The audit checks file and annotation consistency. It does **not** prove that every source label is semantically correct, and it does not create a V2 training split or train a model.

## Source acquisition

- Acquisition date: 2026-09-02
- Source-provided image splits: `train` (6,000 images), `validation` (1,000 images), and `test` (1,000 images)
- Annotation files: one matching `metadata.jsonl` file per split
- Original labels: longitudinal crack, transverse crack, alligator crack, pothole, manhole cover, longitudinal patch, and transverse patch

## Command used

```text
python -B -u src/audit_svrdd.py \
  --extracted-dir data/raw/v2/svrdd/extracted \
  --metadata-dir data/raw/v2/svrdd/metadata \
  --output data/raw/v2/svrdd/svrdd_audit.json \
  --data-label data/raw/v2/svrdd
```

## Results

| Check | Result |
| --- | --- |
| Readable images | 8,000 of 8,000 |
| Image-to-metadata filename agreement | Passed for all splits |
| Image dimensions matching metadata | Passed for all splits |
| Valid absolute and normalized YOLO boxes | 20,804 valid boxes |
| Exact duplicate image content across supplied splits | 0 groups |
| Repeated source image IDs | 0 groups |
| Unlabelled images | 0 |

### Annotation totals

| Source class | Objects |
| --- | ---: |
| Longitudinal crack | 4,665 |
| Transverse crack | 3,404 |
| Alligator crack | 1,728 |
| Pothole | 918 |
| Manhole cover | 3,339 |
| Longitudinal patch | 4,128 |
| Transverse patch | 2,622 |

## Important interpretation

The source contains substantially fewer pothole objects than several other classes. This is an observed source distribution, not a reason to alter source labels or tune on the supplied test split.

The source does not provide dedicated labels for shadows, puddles, stains, clean asphalt, or unpaved road. It therefore cannot by itself teach the planned V2 system to distinguish all pothole look-alikes.

## Boundary rounding note

Twenty-six source absolute boxes ended at `1024.001` on a 1,024-pixel image edge. The corresponding excess was only 0.001 pixel, which is source floating-point rounding. The audit permits at most 0.01 pixel of boundary rounding but still rejects boxes meaningfully outside an image.

## Remaining work before V2 modeling

1. Review a stratified visual sample from each source class.
2. Document how each source label maps to the V2 multi-class, multi-label, and object-detection targets.
3. Acquire and audit a separately licensed look-alike supplement for shadows, puddles, road markings, stains, clean asphalt, and unpaved road.
4. Perform duplicate and source-overlap checks again after all sources are combined.
5. Create a new V2 split. The supplied SVRDD `test` split must not automatically become V2's final protected test.
