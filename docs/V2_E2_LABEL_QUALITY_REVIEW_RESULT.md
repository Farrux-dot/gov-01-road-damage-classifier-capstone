# V2-E2 Label-Quality Review Result

## Scope

This review covers the 233 incorrect V2-E2 validation predictions whose
supplied class is 'crack', 'pothole', or 'repaired_road'. It is a targeted
error sample, not a random dataset-wide label-quality estimate.

The user reviewed every image in the local review page on 2026-09-25. The
decisions were recovered from completed_label_review.pdf; three missed
selection boxes were supplied explicitly afterward by the user.

The protected test set was not loaded. No source image, split, label, or model
was changed.

## Review decisions

| Decision | Images | Share of 233 |
|---|---:|---:|
| visible_and_supported | 190 | 81.5% |
| visible_but_competing_condition | 31 | 13.3% |
| not_visible_at_image_level | 12 | 5.2% |
| needs_source_verification | 0 | 0.0% |

| Supplied label | Visible and supported | Competing condition | Not visible at image level | Total |
|---|---:|---:|---:|---:|
| crack | 60 | 21 | 0 | 81 |
| pothole | 50 | 10 | 4 | 64 |
| repaired_road | 80 | 0 | 8 | 88 |

## Meaning

Most reviewed examples visibly support their supplied image-level label. The
V2-E2 mistakes therefore cannot be explained simply by widespread wrong
labels.

The 31 competing-condition images explain the strongest recurring confusion:
a single road image can visibly contain both a crack and a repaired area, or
both a crack and a pothole. This is a limitation of forcing one main class
onto a scene with more than one road condition.

The 12 not_visible_at_image_level records remain an evidence flag. They are
not automatically deleted or relabeled because a source target may be valid
but too small for honest full-image classification.

## Decision

**Retain the current V2 data and labels unchanged for now.** This focused
review does not authorize automatic exclusions, relabeling, or split changes.

The completed review supports moving to a controlled V2-E3 MobileNetV2
fine-tuning experiment. It must use the same train/validation split, keep the
protected test untouched, and report whether the model improves the still
weak classes without claiming that the 99% F1 target has been reached.
