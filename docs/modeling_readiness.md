# Modeling Readiness Plan

## Purpose

This document records the planned modeling work for GOV-01 before any model is trained. It follows the Module 8 workflow: inspect the data, plan the experiment, train one model at a time, evaluate only on unseen data, and keep evidence in the repository.

## Data Gate position

The project uses the derived clean split at `data/processed/clean_split/`, not the supplied test folder. The clean split contains 1,228 unique labeled images with no exact-hash overlap across splits.

| Split | Images | Normal | Pothole | Use |
| --- | ---: | ---: | ---: | --- |
| Train | 860 | 236 | 624 | Learn model parameters |
| Validation | 185 | 51 | 134 | Choose model settings and compare experiments |
| Test | 183 | 50 | 133 | Final one-time unseen evaluation |

The preprocessing notebook has been run in Google Colab by the student. Before training, retain a screenshot or Colab output showing that the three datasets loaded and that random augmentation applies only to training images.

## Scope boundary

The model predicts only the presence of a pothole: `Normal` or `Pothole`.

It does **not** measure pothole size, physical danger, road safety, repair cost, severity, or repair priority. A human reviewer remains responsible for every operational decision.

## Planned experiments

| Order | Experiment | Why it is included | Decision rule |
| --- | --- | --- | --- |
| 1 | Compact CNN trained from scratch | Honest baseline showing what this dataset can achieve without pretrained knowledge | Record validation metrics and learning curves |
| 2 | Frozen ImageNet-pretrained MobileNetV2 | Main transfer-learning approach; useful for a modest image dataset | Compare against the baseline using validation macro F1 and error patterns |
| 3 | Selective MobileNetV2 fine-tuning | Improvement attempt only if the frozen model is stable and validation results justify it | Keep it only if validation macro F1 improves without clear overfitting |

Training will use the same seed (`42`), image size (`224 x 224`), clean split, and preprocessing boundary recorded in `docs/preprocessing_manifest.json`.

## Evaluation plan

The primary comparison metric is **macro F1** because the two classes are imbalanced. It gives equal importance to `Normal` and `Pothole` rather than letting the more common pothole class dominate the score.

Supporting evidence for every experiment:

- Accuracy, precision, recall, macro F1, and ROC-AUC.
- Confusion matrix and a small review of false positives and false negatives.
- Training/validation learning curves.
- Training time and key hyperparameters.
- Final test metrics only for the selected final model; test data will not guide model selection.

## Stop and safety rules

- Do not use the supplied raw `test` folder because the audit found duplicate leakage.
- Do not tune against the derived test split.
- Do not claim results until the notebook produces them and the output is saved as evidence.
- Stop a run if validation loss rises consistently while training loss improves; record this as possible overfitting.
- If transfer learning does not improve validation macro F1 or produces unacceptable errors, report that honestly rather than forcing a result.

## Next implementation task

Create a dedicated Colab modeling notebook for **Experiment 1 only**: the compact CNN baseline. It should load the prepared datasets, train with early stopping, save learning curves and validation metrics, and leave the clean test split untouched.
