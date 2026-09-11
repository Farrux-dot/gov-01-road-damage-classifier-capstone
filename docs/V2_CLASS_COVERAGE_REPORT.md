# V2 Class Coverage Report

**Report date:** 2026-09-11  
**Stage:** data coverage review before final splitting or training  
**Training status:** not approved

## Purpose

This report compares the data currently available for the planned V2 road-condition labels. It answers three questions:

1. Which labels have traceable candidate data?
2. What kind of evidence exists for each label: full images, object boxes, or reviewed crops?
3. What is still missing before a leakage-safe split and model training can begin?

The report does not copy images, change labels, create train/validation/test folders, or train a model.

## Important counting rule

The following counts are intentionally kept separate:

- **Full-image record:** one complete road photograph.
- **Positive-image record:** one photograph that contains a condition. A multi-label image can count for more than one condition.
- **Object:** one labelled condition inside a photograph, recorded with a box.
- **Crop:** a smaller image cut from a source photograph around one labelled object.
- **Split group:** the original source photograph. All crops from the same photograph must stay in the same future split.

Adding these different units together would create a false total, so this report does not do that.

## Source boundary

The source-traceable candidate inventory contains 6,733 full-image records:

| Source | Candidate records | Current role |
| --- | ---: | --- |
| SVRDD source training split | 6,000 | Four mapped road-condition labels with object boxes |
| V1 clean training Pothole | 624 | Image-level pothole labels without object boxes |
| PaveBench approved detection review | 109 | Individually reviewed candidates with boxes |
| **Total** | **6,733** | Pre-split candidates, not a training dataset |

The V1 validation and protected-test images and the SVRDD source validation and test records remain outside this inventory.

## Multi-class full-image coverage

Multi-class classification gives one main label to each complete image. These counts use the documented priority rule when several conditions appear in the same photograph.

| Main label | SVRDD | V1 | PaveBench | Total candidate images | Evidence note |
| --- | ---: | ---: | ---: | ---: | --- |
| `pothole` | 472 | 624 | 0 | **1,096** | V1 images are 64 x 64 and have no boxes. PaveBench potholes are excluded. |
| `crack` | 3,907 | 0 | 98 | **4,005** | PaveBench contributes only individually approved Alligator and Crack records. |
| `repaired_road` | 1,620 | 0 | 11 | **1,631** | A separate reviewed repaired-road crop pool is described below. |
| `manhole_cover` | 1 | 0 | 0 | **1** | This is a priority-rule collapse, not a claim that SVRDD contains only one manhole. |
| `unpaved_road` | 0 | 0 | 0 | **0** | No accepted dedicated source. |
| `shadow` | 0 | 0 | 0 | **0** | No accepted dedicated source. |
| `puddle` | 0 | 0 | 0 | **0** | No accepted dedicated source. |
| `road_marking` | 0 | 0 | 0 | **0** | No accepted dedicated source. |
| `road_stain` | 0 | 0 | 0 | **0** | No accepted dedicated source. |
| `normal_asphalt` | 0 | 0 | 0 | **0** | V1 Normal images were rejected for V2 because their 64 x 64 resolution does not support a reliable clean-asphalt decision. |

These counts show that the original full-image priority labels are not suitable for the planned ten-class model. Six required classes have no accepted examples, and the priority rule hides manholes inside images labelled as pothole, crack, or repaired road.

## Multi-label positive-image coverage

Multi-label classification can record more than one visible condition in the same image. The counts below are positive-image records, so one image may appear in several rows.

| Positive condition | SVRDD | V1 | PaveBench | Total positive images | Current limitation |
| --- | ---: | ---: | ---: | ---: | --- |
| `pothole_present` | 472 | 624 | 0 | **1,096** | V1 supplies only a pothole image label, not object boxes. |
| `crack_present` | 4,253 | 0 | 98 | **4,351** | PaveBench records were approved for their named class, not exhaustively reviewed for every possible condition. |
| `repaired_patch_present` | 2,077 | 0 | 11 | **2,088** | Quality varies; a separate crop audit provides stronger evidence for repaired roads. |
| `manhole_present` | 1,688 | 0 | 0 | **1,688** | Many targets are small in the source images. |
| `unpaved_surface_present` | 0 | 0 | 0 | **0** | No accepted labelled source. |
| `shadow_present` | 0 | 0 | 0 | **0** | No accepted labelled source. |
| `puddle_present` | 0 | 0 | 0 | **0** | No accepted labelled source. |
| `road_marking_present` | 0 | 0 | 0 | **0** | No accepted labelled source. |
| `road_stain_present` | 0 | 0 | 0 | **0** | No accepted labelled source. |

`Normal_asphalt` cannot be derived yet because six required look-alike or surface labels are missing. The available records also have different annotation completeness: SVRDD maps all four supplied source conditions, while V1 and PaveBench do not prove the absence of every other V2 condition.

## Object-detection coverage

Object detection counts labelled objects, not images. Only records with boxes are included.

| Detection label | SVRDD objects | PaveBench objects | Total candidate objects | Current limitation |
| --- | ---: | ---: | ---: | --- |
| `pothole` | 679 | 0 | **679** | The 624 V1 pothole images cannot be added because they have no boxes. |
| `crack` | 7,335 | 98 | **7,433** | Thin cracks are only approximately represented by rectangular boxes. |
| `repaired_road` | 5,089 | 11 | **5,100** | Sample auditing supports the label, but not every source box was individually reviewed. |
| `manhole_cover` | 2,517 | 0 | **2,517** | Many source targets are small; only a reviewed crop subset is approved below. |
| `unpaved_surface` | 0 | 0 | **0** | No accepted boxes. |
| `shadow_region` | 0 | 0 | **0** | No accepted boxes. |
| `puddle` | 0 | 0 | **0** | No accepted boxes. |
| `road_marking` | 0 | 0 | **0** | No accepted boxes. |
| `road_stain` | 0 | 0 | **0** | No accepted boxes. |

The largest current object class, crack, has about 10.9 times as many objects as pothole. This is a class-imbalance warning, not a model result. The data is also not proven to contain exhaustive boxes for every visible V2 condition in every image.

## Reviewed single-condition crop pools

The crop pools address the multi-class problem caused by mixed-condition full images. They are separate from the full-image and object totals above.

| Crop label | Retained crops | Original source-image groups | Human-review evidence | Current decision |
| --- | ---: | ---: | --- | --- |
| `manhole_cover` | **101** | **97** | All 101 were individually approved; 50 retain a low-resolution review warning. | Keep as candidates, but the pool is small and is not a final split. |
| `repaired_road` | **2,643** | **1,508** | 142 individually approved; 2,501 source-labelled and supported by the 100-sample audit. | Keep as candidates; split by original source-image group. |

Repaired-road crops outnumber approved manhole crops by about 26.2 to 1. Class weighting or sampling can help during a later experiment, but it cannot replace missing variety or create reliable labels.

No reviewed single-condition crop pool currently exists for crack or pothole.

## Coverage decision by planned task

| Planned task | Coverage decision | Reason |
| --- | --- | --- |
| Ten-class multi-class model | **Blocked** | Six labels have zero accepted examples, and the current full-image priority rule collapses manholes. |
| Nine-output multi-label model | **Blocked** | Only four positive conditions are represented; required look-alike labels and trustworthy all-negative `Normal_asphalt` examples are missing. |
| Nine-class object detector | **Blocked** | Only four object classes have boxes, pothole has the fewest boxes, and annotation completeness across all visible conditions is not yet proven. |
| Four-condition research pilot | **Possible after more preparation** | Pothole, crack, repaired road, and manhole have traceable candidates, but formats, quality evidence, class balance, and split groups still need to be standardized. This pilot would not meet the final requirement to distinguish shadows, puddles, stains, markings, unpaved roads, and normal asphalt. |

## What is ready

- Candidate provenance is recorded for the current three sources.
- Only source training data enters the candidate inventory.
- V1 and SVRDD evaluation records remain reserved.
- The 2,643 repaired-road crops and 101 manhole crops preserve original-image split groups.
- PaveBench candidates are restricted to individually approved records.
- Exact-duplicate evidence already exists for the original inventory and repaired-road crop pool.

## What is not ready

1. Dedicated accepted data for `unpaved_road`, `shadow`, `puddle`, `road_marking`, `road_stain`, and `normal_asphalt`.
2. A common image format and quality rule across pothole, crack, repaired-road, and manhole candidates.
3. A reviewed single-condition crop pool for pothole and crack if the multi-class experiment uses crops.
4. A final group-based train, validation, and protected-test split.
5. A post-split class-balance report.
6. Proof that detection annotations cover every applicable object in retained images.
7. A frozen V2 task scope and success criteria.

## Recommended next task

Define a leakage-safe group split plan for the four currently represented conditions without creating the split yet. The plan must:

- keep every crop from one original image in one split;
- keep related source frames together when a reliable source group is available;
- preserve V1 and SVRDD reserved evaluation data;
- state how the 624 V1 pothole images without boxes are handled for each task;
- report the expected class and source counts per split before materialization;
- keep the six missing labels blocked rather than silently treating them as negative.

Training remains blocked until the selected task has complete labels, a documented split, and a completed Data Gate.

## Evidence files

- `docs/v2_candidate_inventory.csv`
- `docs/V2_CANDIDATE_INVENTORY.md`
- `docs/v2_pavebench_detection_review_manifest.csv`
- `docs/V2_PAVEBENCH_DETECTION_DATA_GATE.md`
- `docs/v2_svrdd_manhole_approved_manifest.csv`
- `docs/V2_MANHOLE_CROP_REVIEW_METHOD.md`
- `docs/v2_svrdd_repaired_road_unique_keep_manifest.csv`
- `docs/v2_svrdd_repaired_road_unique_quality_exclusions.csv`
- `docs/V2_REPAIRED_ROAD_DEDUPLICATION_AND_QUALITY_REVIEW.md`
- `docs/V2_V1_INTEGRATION_AUDIT.md`
- `docs/V2_ROAD_CONDITION_LABELING_GUIDE.md`
