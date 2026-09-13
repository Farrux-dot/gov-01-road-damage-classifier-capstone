# V2 CeyMo Structural Data Audit

## Scope

This audit covers the downloaded CeyMo **training set only**. Raw ZIP files,
images, annotations, masks, and the machine-readable JSON audit remain in the
Git-ignored `data/raw/v2/ceymo/` folder.

The audit checks file readability, annotation agreement, geometry, and exact
duplicates. It does not create a final split, change raw labels, train a model,
or evaluate model performance.

## Source and acquisition

- Official source: [oshadajay/CeyMo](https://github.com/oshadajay/CeyMo)
- Paper: [CeyMo: See More on Roads](https://openaccess.thecvf.com/content/WACV2022/html/Jayasinghe_CeyMo_See_More_on_Roads_-_A_Novel_Benchmark_Dataset_WACV_2022_paper.html)
- Download date: 2026-09-13
- Downloaded part: official train set, 2,099 images
- Image resolution: 1,920 x 1,080
- Source annotations: LabelMe polygon JSON, Pascal VOC-style XML boxes, and PNG segmentation masks
- Licence evidence: the official repository contains an MIT licence. Confirm that it covers dataset-file redistribution before redistributing any images; raw images are not committed here.
- Human sample decision: the student reviewed supplied examples and confirmed that the image quality and road-marking examples were suitable for the V2 purpose.

The official CeyMo test set was not downloaded or used. This prevents it from
being accidentally used during V2 data preparation.

## Reproducible command

```text
python -B -m src.audit_ceymo \
  --data-dir data/raw/v2/ceymo/train/extracted/train \
  --output data/raw/v2/ceymo/ceymo_train_audit.json \
  --data-label data/raw/v2/ceymo/train/extracted/train
```

## Verified results

| Check | Result |
| --- | ---: |
| Readable JPG images | 2,099 of 2,099 |
| Readable PNG masks | 2,099 of 2,099 |
| XML annotation files | 2,099 |
| Polygon JSON files | 2,099 |
| Missing or extra annotation counterparts | 0 |
| XML road-marking objects | 3,488 |
| Polygon road-marking objects | 3,488 |
| XML-to-polygon label disagreements | 0 images |
| Invalid XML boxes | 0 |
| Invalid polygons beyond the accepted one-pixel tolerance | 0 |
| Unknown labels | 0 |
| Exact duplicate image groups | 2 |
| Redundant image files beyond the first copy | 2 |

All images and masks are 1,920 x 1,080 pixels.

### Observed source-label counts

| Source label | Official meaning | Observed objects |
| --- | --- | ---: |
| `BL` | Bus Lane | 142 |
| `CL` | Cycle Lane | 61 |
| `DM` | Diamond | 770 |
| `JB` | Junction Box | 128 |
| `LA` | Left Arrow | 118 |
| `PC` | Pedestrian Crossing | 611 |
| `RA` | Right Arrow | 260 |
| `SA` | Straight Arrow | 1,088 |
| `SL` | Slow | 72 |
| `SLA` | Straight-Left Arrow | 180 |
| `SRA` | Straight-Right Arrow | 58 |
| **Total** |  | **3,488** |

## Warnings that must remain visible

1. `119a.json` contains one polygon point at approximately `x=-0.94`. This is
   less than one pixel outside the image and is treated as source boundary
   rounding. A future converter may clip it to the image edge but must not edit
   the raw annotation.
2. `179a.json` contains `imagePath="179.jpg"` although the verified matching
   image is `179a.jpg`. Future conversion must pair records by the verified file
   stem, not by that one metadata value.
3. Exact duplicate pairs are `602b.jpg`/`615b.jpg` and
   `605.jpg`/`618c.jpg`. Duplicate copies must be removed or kept in the same
   split group before any train/validation/test split.
4. The archive contains 142 `BL` and 61 `CL` objects, while the official paper
   reports the train counts in the opposite order. Both labels map to the same
   V2 `road_marking` class, so this does not affect the general V2 condition.
   Do not claim reliable Bus-Lane-versus-Cycle-Lane subtype training until the
   discrepancy is resolved.

## Data Gate decision

**Structural audit: PASSED WITH WARNINGS.**

CeyMo is accepted as a source-labelled candidate pool for the general V2
`road_marking` condition. It provides road-marking presence labels and object
locations. It does not prove that other planned road conditions are absent from
an image, so it cannot automatically supply complete nine-output multi-label
truth or a final multi-class primary label.

No final V2 split has been created, and no V2 model has been trained.

## Next controlled step

Build a source-traceable CeyMo candidate manifest, remove or group the two
duplicate copies, and preserve original source filenames. Only then may the
accepted records be integrated into the combined V2 pre-split inventory.

