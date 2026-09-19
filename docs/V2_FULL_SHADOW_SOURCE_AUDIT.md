# V2 Full SRD and ISTD Shadow-Source Audit

**Audit date:** 2026-09-19  
**Stage:** completed structural audit; not integrated into a training split

## What was checked

Every downloaded record was read directly from its source Parquet file. For
each record, the audit verified that all three files are readable:

1. the original image containing a shadow;
2. the shadow mask, which marks the shadow area; and
3. the shadow-free target image supplied by the source.

The detailed traceable result is
`docs/v2_full_shadow_source_audit_manifest.csv`. It contains paths, source
split, image size, hashes, mask coverage, and a safety status for every
record. It does not contain copied images or model output.

## Verified structural results

| Source | Train records | Source-test records | Total | Exact duplicate result |
| --- | ---: | ---: | ---: | --- |
| SRD, local Hugging Face mirror | 2,675 | 406 | 3,081 | One exact duplicate group containing two images |
| ISTD, local Hugging Face mirror | 1,330 | 540 | 1,870 | No exact duplicate images |
| **Total** | **4,005** | **946** | **4,951** | One duplicate group in SRD |

All 4,951 records have readable original images, masks, and targets. Mask
coverage is not used to decide road quality; it merely confirms the source
mask contains a measurable marked region.

## What this audit does *not* prove

SRD and ISTD are shadow-removal datasets. They include many useful shadow
patterns, but they are not automatically all road scenes. Therefore this audit
does **not** claim that every source image is suitable for the GOV-01 road
classifier.

The records are deliberately marked:

`structurally_valid_not_integrated`

This means “the files are real and readable,” not “ready to train.”

## Safety rules going forward

- Keep the 406 SRD and 540 ISTD source-test records protected. They must not
  be added to V2 training or used to tune a model.
- Do not add all 4,951 images directly to the road-condition inventory. First
  apply a road-context filter and remove sequence/near-duplicate risk.
- Confirm original-source provenance and licence conditions before any training
  use. The local mirror README says MIT, but it also calls both mirrors
  unofficial.
- Treat SRD/ISTD as **supporting shadow-pattern sources**, not pothole, crack,
  manhole, asphalt, or unpaved-road class sources.

## Plain-language conclusion

We now know the full downloads are structurally complete: the shadows and
their masks are available and readable. The next job is not training. It is to
select only the road-relevant, duplicate-safe training portion after the
licence/provenance and road-context rules are resolved.
