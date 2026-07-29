# Technical proposal: GOV-01

## Problem and stakeholder

A municipal infrastructure department receives road photographs from inspectors and citizens. Manual review can be slow and inconsistent. The intended user is a municipal staff member who needs help prioritizing reports for human inspection.

## Proposed ML formulation

Binary supervised image classification: predict `Normal` (0) or `Pothole` (1) from one road image. The model output is a probability and predicted class. The prediction supports triage only and cannot establish road safety, severity, or repair priority.

## Data plan

Use the selected Kaggle Pothole Detection Dataset. Audit the official downloaded files before training for class counts, corrupt images, split consistency, and exact duplicate images between splits. Do not alter the provided test set. If leakage is found, create a documented stratified split from the de-duplicated source images.

## Experiment plan

1. Baseline: compact CNN trained from scratch.
2. Main approach: ImageNet-pretrained MobileNetV2, frozen feature extractor.
3. Improvement experiment: unfreeze selected MobileNetV2 layers after initial training, if validation results justify it.
4. Compare macro F1, precision, recall, accuracy, ROC-AUC, training time, and error patterns.

## Success criteria

The final model must outperform the baseline on held-out macro F1, produce a reproducible prediction from a new image, and include honest analysis of false positives and false negatives. No target score will be claimed before experiments are run.

## Risks and mitigation

- **Class imbalance:** report class counts; use class weights only if justified.
- **Leakage:** hash images across splits before training.
- **Distribution shift:** examine difficult cases such as blur, shadow, rain, non-asphalt surfaces, unusual camera angles, and damaged roads unlike the training data.
- **False confidence:** show probability, document limitations, and retain human review.
- **Privacy:** do not publish images with identifying personal data without permission.
