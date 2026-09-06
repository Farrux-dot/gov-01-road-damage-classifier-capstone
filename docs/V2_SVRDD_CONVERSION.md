# V2 SVRDD Annotation Conversion

## What this step does

The conversion tool reads SVRDD JSONL annotations and creates a new V2-ready JSONL file for each source split:

- `train.v2.jsonl`
- `validation.v2.jsonl`
- `test.v2.jsonl`

It does **not** change the raw SVRDD annotations or images. It does **not** create the final V2 train/validation/test split, and it does **not** train a model.

Each converted record preserves the source image identifier, image dimensions, and object box coordinates. It adds:

- the mapped V2 object label for every source box;
- four V2 multi-label Yes/No fields;
- one source-derived V2 multi-class label using the documented SVRDD-only priority rule.

## Safety checks

The tool stops instead of creating partial data when:

- a JSON line is invalid;
- required source fields are missing;
- source object lists have different lengths;
- a source category ID does not match its expected source category name;
- a source label is unsupported.

## Run command

Run from the repository root after the raw metadata files are present:

```text
python -B src/convert_svrdd_to_v2.py \
  --metadata-dir data/raw/v2/svrdd/metadata \
  --output-dir data/processed/v2/svrdd/annotations \
  --report data/processed/v2/svrdd/conversion_report.json
```

The `data/processed/` folder is ignored by Git. The converted files are reproducible derived data, not files to upload or commit.

## Interpretation boundary

The converted SVRDD data supports only these four V2 conditions: `pothole`, `crack`, `manhole_cover`, and `repaired_road`.

It still does not provide dedicated examples for shadows, puddles, stains, road markings, clean asphalt, or unpaved roads. A separate licensed and audited source is required before those planned V2 labels can be trained.

## Results

Conversion run date: 2026-09-06.

| Check | Result |
| --- | --- |
| Source records converted | 8,000 of 8,000 |
| Derived training records | 6,000 |
| Derived validation records | 1,000 |
| Derived test records | 1,000 |
| V2 objects after conversion | 20,804 |
| Missing derived records | 0 |

### V2 object totals

| V2 condition | Objects |
| --- | ---: |
| `crack` | 9,797 |
| `repaired_road` | 6,750 |
| `manhole_cover` | 3,339 |
| `pothole` | 918 |

The four object totals equal the 20,804 source objects recorded during the structural audit. This confirms that no object category was dropped during conversion.

The converted data is still source-provided data. These counts must not be used to choose a final V2 model, tune against the supplied test split, or claim that the future combined V2 dataset is ready for training.
