# V2 SVRDD Label Mapping

## Purpose

SVRDD has seven original annotation names. This document defines the exact, reproducible conversion from those seven names into the four V2 road-condition labels that SVRDD can currently support:

1. `pothole`
2. `crack`
3. `manhole_cover`
4. `repaired_road`

This is a source-mapping rule only. It does not modify raw annotations, create a split, train a model, or change V1.

## Exact source mapping

| SVRDD original annotation | V2 condition | Why |
| --- | --- | --- |
| `pothole` | `pothole` | A physical road hole or depression. |
| `longitudinal crack` | `crack` | One type of visible road crack. |
| `transverse crack` | `crack` | One type of visible road crack. |
| `alligator crack` | `crack` | A network/clustered road crack pattern. |
| `manhole cover` | `manhole_cover` | A manufactured utility cover, not road damage. |
| `longitudinal patch` | `repaired_road` | A repaired/filled road area along the road direction. |
| `transverse patch` | `repaired_road` | A repaired/filled road area across the road direction. |

## Why `manhole_cover` is separate

A manhole cover gives workers access to underground utilities such as sewer, water, or communication lines. It is usually circular or rectangular and may be dark or surrounded by rough asphalt. It can resemble a pothole in a photo, but it is an intentional road fixture rather than a hole that needs repair.

Keeping `manhole_cover` separate helps prevent a model from reporting utility covers as potholes.

## Use in each V2 approach

### Multi-class classification

Multi-class produces one main condition per image. When an SVRDD image has several of the four mapped conditions, use this **SVRDD-only priority order**:

1. `pothole`
2. `crack`
3. `repaired_road`
4. `manhole_cover`

Example: an image with a pothole, crack, and manhole cover gets the one main label `pothole`.

This four-label priority rule is only for records derived from SVRDD. The broader V2 guide may later include additional look-alike classes when separately sourced and audited data is available.

### Multi-label classification

One image can have more than one Yes/No result:

- `pothole_present`
- `crack_present`
- `manhole_cover_present`
- `repaired_road_present`

Example: a photo containing a pothole and cracks becomes `pothole_present=Yes` and `crack_present=Yes`.

### Object detection

Every SVRDD box remains a separate object box. Only its class name changes according to the mapping table. Multiple crack types become the object class `crack`; multiple patch types become `repaired_road`.

## Explicit non-mapping rules

SVRDD does not have a dedicated `shadow`, `puddle`, `road_stain`, `road_marking`, `normal_asphalt`, or `unpaved_road` source label. This mapping must never invent those labels from an SVRDD image.

Likewise, an unsupported source label must stop conversion with an error rather than being silently guessed. The automated check in `tests/test_svrdd_v2_mapping.py` enforces this.

## Verification

Run the focused mapping check from the repository root:

```text
python -B -m unittest discover -s tests -p "test_svrdd_v2_mapping.py" -v
```

The test confirms that all seven known SVRDD source labels map to exactly the four agreed V2 conditions, that multi-label output can contain multiple conditions, and that unsupported labels are rejected.
