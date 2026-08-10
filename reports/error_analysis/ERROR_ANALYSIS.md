# Final V1 Error Analysis

## Purpose

This document explains the errors made by the final assessed model, `mobilenetv2_frozen_v4`, on the protected Version 1 clean test split. It does not change the final model, threshold, or test result.

## Evaluation boundary

- **Task:** classify one road image as `Normal` or `Pothole`.
- **Protected test:** 183 previously unseen images: 50 `Normal` and 133 `Pothole`.
- **Decision threshold:** pothole probability at or above `0.50` is classified as `Pothole`.
- **Final test result:** Macro F1 `0.939901`; accuracy `0.950820`.
- **Evidence:** `reports/model_gate.md` and `reports/mobilenetv2_frozen_v4_protected_test_confusion_matrix.png`.

## Confusion-matrix interpretation

| True image class | Predicted Normal | Predicted Pothole | Meaning |
|---|---:|---:|---|
| Normal | 48 | 2 | Two false pothole alerts. |
| Pothole | 7 | 126 | Seven potholes were missed. |

The model made 9 classification errors among 183 protected-test images. This is strong performance on this particular clean split, but it is not perfect performance and it does not prove reliability on every real municipal road photo.

## Error types and operational impact

### Missed potholes: false negatives

Seven true pothole images were predicted as `Normal`. In a report-triage setting, this is the more serious error because an image could receive less attention even though it contains a pothole.

**Mitigation:** a `Normal` model output must not automatically close, dismiss, or deprioritize a citizen or inspector report. Municipal staff should retain human review, especially when the image is unclear or a report contains additional context.

### False pothole alerts: false positives

Two true `Normal` images were predicted as `Pothole`. This can create extra human-review work, but it is safer than automatically rejecting a genuine pothole report.

**Mitigation:** treat a `Pothole` output as a preliminary flag for review, not as proof that a repair is required.

## What this analysis can and cannot claim

The final evidence records the number of each error type, but it does not retain a reviewed list of individual test-image IDs or proven visual causes for each error. Therefore, this project does **not** claim that a particular false result was caused by a shadow, a repaired road, a crack, blur, rain, or a camera angle.

Those conditions remain plausible deployment risks because the dataset is small and low resolution, but they require a future, documented slice analysis with separately labelled examples before making a stronger claim.

## Generalization limits that affect errors

- Source images are only `64 x 64` pixels before model resizing, so visual detail is limited.
- The original supplied folders contained duplicates; a clean exact-hash split was rebuilt. This prevents exact duplicate leakage, but the source has no scene, location, or repeated-subject metadata, so near-duplicate scene leakage cannot be ruled out completely.
- The dataset may not represent all lighting, weather, road surfaces, camera angles, damage types, or geographic locations found in real municipal reports.
- The test split comes from the same source dataset as training and validation. It is not an external municipal deployment study.

## Final decision

`mobilenetv2_frozen_v4` remains the final assessed V1 model because it was selected using validation evidence and then evaluated once on the protected clean test split. Its output is suitable only as **human-review triage support**. It must not be used as an automatic safety, repair-priority, severity, or road-condition decision.
