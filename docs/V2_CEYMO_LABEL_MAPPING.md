# V2 CeyMo Road-Marking Label Mapping

## Purpose

CeyMo distinguishes 11 kinds of road markings. GOV-01 V2 currently needs one
general condition called `road_marking`. This document defines how the source
labels are converted without guessing or changing the raw annotations.

## Exact mapping

| CeyMo label | Official source meaning | V2 detection condition |
| --- | --- | --- |
| `BL` | Bus Lane | `road_marking` |
| `CL` | Cycle Lane | `road_marking` |
| `DM` | Diamond | `road_marking` |
| `JB` | Junction Box | `road_marking` |
| `LA` | Left Arrow | `road_marking` |
| `PC` | Pedestrian Crossing | `road_marking` |
| `RA` | Right Arrow | `road_marking` |
| `SA` | Straight Arrow | `road_marking` |
| `SL` | Slow | `road_marking` |
| `SLA` | Straight-Left Arrow | `road_marking` |
| `SRA` | Straight-Right Arrow | `road_marking` |

The original abbreviation must be preserved in traceability metadata even when
the model-facing label becomes `road_marking`.

## Use in the three planned approaches

### Multi-class classification

Do **not** automatically give every complete CeyMo image the primary label
`road_marking`. CeyMo confirms that a marking is present, but it does not label
every possible pothole, crack, puddle, shadow, stain, repair, or manhole in the
same scene. The final one-label priority rule therefore requires additional
cross-condition review before a CeyMo image can become a multi-class record.

### Multi-label classification

At least one verified CeyMo annotation means:

```text
road_marking_present = Yes
```

The other planned Yes/No outputs remain **unknown**, not automatically `No`,
until the complete image is reviewed for those conditions.

### Object detection

Every valid CeyMo marking object can be converted to the general box label
`road_marking`. CeyMo also supplies polygon ground truth and masks, but the
current V2 object-detection target uses boxes. The detailed CeyMo subtype should
remain available as metadata for audit and possible future research.

## Safety rules

1. Reject an unknown CeyMo source label instead of guessing its meaning.
2. Do not convert road markings into potholes, cracks, stains, or repairs.
3. Pair `179a.json` by verified file stem because its internal `imagePath` is inconsistent.
4. Clip the subpixel boundary rounding in `119a.json` only in a derived conversion; never edit the raw source annotation.
5. Remove or group exact duplicates before splitting.
6. Do not use the official CeyMo test set for training or tuning.
7. Do not claim detailed `BL` versus `CL` subtype reliability until their count discrepancy is resolved.

## Automated verification

```text
python -B -m unittest tests.test_ceymo_v2_mapping tests.test_audit_ceymo -v
```

The tests verify the 11-label mapping, reject unsupported labels, check empty
and positive multi-label behavior, validate XML boxes, and distinguish harmless
subpixel polygon rounding from a meaningful boundary error.

