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

The unweighted CNN restored its best validation-loss weights after seven epochs and took 1,248.6 seconds to train. Its validation confusion matrix had 240 true `No_pothole` predictions, zero false pothole predictions, 108 missed potholes, and zero correctly detected potholes. It did not improve on the naive reference.

**Next action:** run `v2_cnn_class_weighted`, keeping the CNN architecture, split, seed, preprocessing, optimizer, and validation metric unchanged while calculating class weights from the training labels only. The protected test remains unloaded.
