# Version 2 Model Gate Plan

## Purpose

This plan defines the first controlled Version 2 model experiments on the Rome Road Damage Dataset. Version 1, its final artifact, and its protected-test result remain unchanged.

## Data boundary

- Training split: 1,398 duplicate-free images (`821` `No_pothole`, `577` `Pothole`).
- Validation split: 348 images (`240` `No_pothole`, `108` `Pothole`).
- Protected test split: 258 images (`151` `No_pothole`, `107` `Pothole`).
- The protected test must not be loaded, used for threshold selection, or used to select a model.

## Metrics

The primary validation metric is **macro F1**. We also record accuracy, pothole precision and recall, no-pothole recall, ROC-AUC, a classification report, and a confusion matrix. Accuracy alone could hide weaker performance on the smaller pothole class.

## Controlled experiment sequence

| Order | Run ID | Purpose | Changed factor | Class weights |
|---:|---|---|---|---|
| 1 | `v2_naive_no_pothole` | Establish a simple reference floor by predicting the validation majority class for every image. | Prediction rule | Not applicable |
| 2 | `v2_cnn_unweighted` | Check whether a compact CNN can learn road-image patterns beyond the naive rule. | CNN model | None |
| 3 | `v2_cnn_class_weighted` | Test whether class weights improve macro F1 and the balance of both recalls. | Class weights only | Calculated from training labels only |
| 4 | `v2_mobilenetv2_frozen` | Test transfer learning against the best compact-CNN baseline. | Model family | Use the chosen V2 weighting rule |

The first compact CNN will use the real training distribution without class weights. This provides an honest reference. The next experiment will keep the split, seed, image size, augmentation, optimizer, architecture, and validation metric fixed while adding class weights.

## Candidate-lock rule

Select one Version 2 candidate using validation evidence only. Lock its architecture, preprocessing, class-weight choice, seed, and threshold before one protected-test evaluation. No retraining or tuning is allowed after protected-test access.

## Current status

Preprocessing was executed and verified in Colab. The first two validation-only reference runs were then completed on 2026-08-08:

| Run ID | Accuracy | Macro F1 | Pothole recall | No-pothole recall | ROC-AUC | Decision |
|---|---:|---:|---:|---:|---:|---|
| `v2_naive_no_pothole` | 0.689655 | 0.408163 | 0.000000 | 1.000000 | 0.500000 | Reference floor only |
| `v2_cnn_unweighted` | 0.689655 | 0.408163 | 0.000000 | 1.000000 | 0.470909 | Reject; it predicted `No_pothole` for every validation image |
| `v2_cnn_class_weighted` | 0.577586 | 0.479609 | 0.231481 | 0.733333 | 0.492940 | Improves macro F1 and detects some potholes, but remains too weak to select |
| `v2_mobilenetv2_frozen` | 0.566092 | 0.538563 | 0.518519 | 0.587500 | 0.548495 | Best V2 validation result so far; continue to fine-tuning, do not test yet |
| `v2_mobilenetv2_finetuned` | 0.557471 | 0.539904 | 0.583333 | 0.545833 | 0.557022 | Current validation leader by Macro F1; select a validation threshold before locking |

The unweighted CNN restored its best validation-loss weights after seven epochs and took 1,248.6 seconds to train. Its validation confusion matrix had 240 true `No_pothole` predictions, zero false pothole predictions, 108 missed potholes, and zero correctly detected potholes. It did not improve on the naive reference.

The class-weighted CNN was trained for six epochs (997.1 seconds). Its class weights were calculated from the 1,398 training images: `No_pothole=0.851`, `Pothole=1.211`. Its validation confusion matrix contains 176 correctly predicted `No_pothole` images, 64 `No_pothole` images predicted as `Pothole`, 83 missed potholes, and 25 correctly detected potholes. Class weighting therefore improves the fair Macro F1 score from `0.408163` to `0.479609` and changes pothole recall from `0.0` to `0.231481`; however, it is not a viable candidate.

When the unweighted CNN was repeated in the later fresh Colab run, its ROC-AUC displayed as `0.477881` rather than the initial `0.470909`. Its accuracy, Macro F1, and threshold predictions were unchanged: it still predicted `No_pothole` for all validation images. This minor score variation is recorded as a repeat observation and does not change the decision.

The frozen MobileNetV2 ran for nine epochs (811.9 seconds) with ImageNet weights frozen and only its 1,281-parameter output head trainable. It correctly detected 56 potholes and missed 52; it correctly labelled 141 `No_pothole` images and incorrectly marked 99 as `Pothole`. This is an improvement over both compact CNNs but it is still not a candidate: the false-positive count and both class recalls need improvement.

The fine-tuned MobileNetV2 unfreezes its final 10 feature-extractor layers while keeping batch-normalization layers frozen. It trained for six epochs (642.7 seconds) with learning rate `1e-5`. At the default 0.50 threshold, it correctly detected 63 potholes and missed 45; it correctly labelled 131 `No_pothole` images and incorrectly marked 109 as `Pothole`. Its Macro F1 is `0.539904`, only `0.001341` above frozen MobileNetV2. The gain comes from higher pothole recall; the trade-off is 10 additional false alerts and lower `No_pothole` recall.

**Next action:** search a small set of decision thresholds using validation probabilities and Macro F1 only. Then lock the selected model configuration and threshold before one protected-test evaluation. The protected test remains unloaded.

## Candidate lock (2026-08-09)

The following threshold search used the fine-tuned MobileNetV2 validation probabilities only. Thresholds from `0.10` to `0.90` in steps of `0.05` were compared using Macro F1. The best result is the default threshold **0.50**:

| Threshold | Validation Macro F1 | Pothole recall | No-pothole recall |
|---:|---:|---:|---:|
| 0.45 | 0.483752 | 0.685185 | 0.395833 |
| **0.50** | **0.539904** | **0.583333** | **0.545833** |
| 0.55 | 0.530026 | 0.407407 | 0.658333 |
| 0.60 | 0.523234 | 0.277778 | 0.770833 |

The candidate is now locked as `v2_mobilenetv2_finetuned` with these settings:

- derived Rome clean split and its fixed capture-group boundaries;
- 224 x 224 RGB input and training-only augmentation;
- binary labels: `No_pothole=0`, `Pothole=1`;
- class weights: `No_pothole=0.851`, `Pothole=1.211`;
- ImageNet MobileNetV2, followed by frozen training and then cautious fine-tuning of its final 10 layers with batch-normalization layers frozen;
- fine-tuning learning rate `1e-5`;
- decision threshold `0.50`.

No protected-test image has been loaded, predicted, or used to make this decision. The next action is one final protected-test evaluation of this locked candidate. No further tuning, threshold changes, or retraining will be allowed afterward.
