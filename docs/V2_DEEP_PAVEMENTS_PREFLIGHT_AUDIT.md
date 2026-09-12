# V2 Deep Pavements Preflight Audit

**Audit date:** 2026-09-11  
**Stage:** source preflight before human review or training  
**Decision:** rejected for the current V2 dataset

## Intended use

Deep Pavements was evaluated as a possible classification source for:

- `Normal_asphalt` from the source `asphalt` folder;
- `Unpaved_road` from the source `compacted`, `gravel`, and `ground` folders.

Only these four relevant folders were extracted. The other six surface classes
were not needed for this preflight.

## Source and licence record

- Source: <https://github.com/kauevestena/deep_pavements_dataset>
- Repository licence: MIT
- Source description: images collected from Wikimedia Commons, Mapillary, and
  Flickr under what the provider describes as CC-compatible licences.
- Download date: 2026-09-11
- Original format: image-level class folders

The repository gives a general source and licence statement, but the extracted
files use hashed names and do not provide a per-image source URL or per-image
licence record. This limits image-level provenance checking.

## Structural results

| Source class | Images | Below 224 pixels on at least one side | Meeting 224-pixel minimum |
| --- | ---: | ---: | ---: |
| `asphalt` | 500 | 468 | 32 |
| `compacted` | 500 | 484 | 16 |
| `gravel` | 500 | 484 | 16 |
| `ground` | 500 | 490 | 10 |
| **Total** | **2,000** | **1,926** | **74** |

Additional checks:

- all 2,000 images are readable PNG files;
- all 2,000 images use RGBA mode;
- 1,343 different resolutions occur;
- the smallest inspected dimensions include `15 x 7`, `27 x 18`, and `32 x 22`;
- no exact SHA-256 duplicate group was found in the four extracted classes;
- no cross-class exact duplicate was found.

## Semantic and quality mismatch

The V2 label `Unpaved_road` requires a complete road scene where the main
visible drivable surface is soil, gravel, sand, or stones. The inspected Deep
Pavements examples are predominantly close surface-texture patches rather than
road-scene photographs. They can show asphalt, gravel, or soil texture, but do
not reliably show that the main driving surface is unpaved.

The same problem affects `Normal_asphalt`: a clean texture patch does not prove
that a full road scene contains none of the nine V2 conditions or look-alikes.

Upscaling the thumbnails to `224 x 224` would enlarge pixels; it would not
restore missing visual information. The source is therefore unsuitable for the
planned V2 road-scene classification tasks.

## Data Gate decision

- Accept **zero** Deep Pavements images into the V2 candidate inventory.
- Do not create a manual review workbook for this source.
- Do not use these files for train, validation, or protected test data.
- Keep the downloaded source only as ignored audit evidence until the user
  decides whether to remove it.
- Continue searching for full road-scene images with an explicit paved/unpaved
  label and traceable licensing.

No V2 model was trained and no existing split was changed.
