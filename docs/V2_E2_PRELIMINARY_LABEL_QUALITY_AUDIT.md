# V2-E2 Preliminary Label-Quality Audit

## Purpose and boundary

This audit reviews the error-analysis output from the frozen MobileNetV2
experiment (`V2-E2`). Its purpose is to determine whether the most serious
validation mistakes are likely to be solved by model tuning alone, or whether
the visible label evidence needs more review first.

It does **not** relabel, delete, move, copy, or otherwise alter any source
image. It does not retrain a model. It uses only the existing V2 validation
split; the protected test split was not loaded.

## Evidence reviewed

The reviewed package was `v2_e2_error_analysis.zip`, created from the saved
V2-E2 checkpoint.

| Item | Verified value |
|---|---:|
| Validation images evaluated | 1,658 |
| Incorrect predictions | 299 |
| Validation accuracy | 0.8197 |
| Validation Macro F1 | 0.8374 |
| Gallery selection | 66 high-confidence incorrect images |

The gallery contains the highest-confidence incorrect examples for every
class below the project's 99% F1 target: 12 each for `crack`,
`normal_asphalt`, `pothole`, `repaired_road`, and `speed_bump`, plus all six
incorrect `unpaved_road` examples. This is an intentionally difficult,
model-selected review sample, not a random sample. It must not be used to
estimate the dataset-wide label-error rate.

## Main confusion evidence

| Supplied validation label | Model prediction | Images |
|---|---|---:|
| `repaired_road` | `crack` | 87 |
| `crack` | `repaired_road` | 55 |
| `pothole` | `crack` | 55 |
| `normal_asphalt` | `crack` | 24 |
| `crack` | `pothole` | 17 |
| `normal_asphalt` | `unpaved_road` | 12 |
| `speed_bump` | `pothole` | 11 |

The largest reciprocal confusion is `crack` versus `repaired_road` (142
images in both directions combined).

## Visual findings

### Crack, repaired road, and pothole

Many selected full-frame road scenes have a supplied `crack`,
`repaired_road`, or `pothole` label, while the named feature is small, distant,
or not clearly visible at the displayed image scale. This is especially common
in the `crack` and `repaired_road` galleries, which contain wide road scenes
that look clean or nearly clean at first inspection.

This does **not** prove that the source label is wrong. A small source
annotation may be correct but become unsuitable when converted to one label
for a whole image. Under the V2 labeling guide, an image cannot honestly be
used as an image-level `crack`, `pothole`, or `repaired_road` example when the
relevant condition is not clearly visible in the image itself.

### Normal asphalt

Several selected `normal_asphalt` examples have unusual visual context:
strong shadow, a narrow path, light/gravel-looking surfaces, or active
construction/repair context. These scenes are plausible reasons for confusion
with `unpaved_road`, `repaired_road`, and `pothole`. They warrant a targeted
mapping and visibility review before assuming the model alone is at fault.

### Speed bump and unpaved road

The gallery includes several visually recognizable speed bumps and unpaved
surfaces. Their errors therefore show genuine visual variation as well as
possible labeling limitations: speed bumps vary from painted raised strips to
low dark bands, and unpaved examples include paths or light gravel surfaces.

## Decision

**Do not claim that a standard V2-E3 fine-tuning run can achieve the 99% F1
target on the current image-level data without first addressing visibility and
label-definition limits.** The evidence supports a targeted data-quality
review before the next training experiment.

No label is changed by this audit. A visually unclear image is not the same
as a proven incorrect source annotation.

## Safest next action

Create a limited, source-traceable review queue for the high-confidence
`crack`, `repaired_road`, and `pothole` errors. For each image, record one of:

1. `visible_and_supported` — the supplied image-level label is clearly
   visible;
2. `visible_but_competing_condition` — more than one road condition is
   visible, so the single-label policy needs an explicit decision;
3. `not_visible_at_image_level` — the source target may exist, but the full
   image is unsuitable for this image-level class; or
4. `needs_source_verification` — the image alone cannot support a decision.

Only after this review should the project decide whether to exclude verified
unclear images, use source crops/boxes where permitted, or proceed to a
carefully controlled fine-tuning experiment. The protected test set remains
untouched throughout model selection.
