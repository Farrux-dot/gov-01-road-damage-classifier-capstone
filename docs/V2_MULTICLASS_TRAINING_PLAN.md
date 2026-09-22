# V2 Multi-Class Training Plan

**Status:** Plan only — no V2 model has been trained.  
**Scope:** Seven-class, image-level road-condition classification. This is not
an object-detection or multi-label plan, and it does not replace frozen V1.

## Purpose

This document fixes the rules for future V2 experiments before training begins.
Its purpose is to make every model comparison fair and to protect the final
test set from influencing model choices.

## Approved materialized data

The final data folders are Git-ignored and were created from the approved
manifest. Raw source images remain unchanged.

| Split | Images | Use |
| --- | ---: | --- |
| `train` | 9,452 | Learn model parameters; augmentation is allowed only here. |
| `validation` | 1,658 | Compare experiments and choose a candidate. |
| `protected_test` | 1,654 | One final evaluation after candidate selection only. |
| Excluded label conflict | 4 | Not used in any experiment. |

Class names and their fixed integer order are:

```text
0 crack
1 manhole_cover
2 normal_asphalt
3 pothole
4 repaired_road
5 speed_bump
6 unpaved_road
```

The data loader must verify this class order against the materialized folder
names before every experiment. The source-to-output traceability record is
`docs/v2_multiclass_final_materialization_manifest.csv`.

## Required experiment boundaries

1. Use only `train` and `validation` until one final candidate is selected.
2. Never use `protected_test` for augmentation, class-weight calculation,
   threshold choice, early stopping, hyperparameter tuning, or comparison.
3. Use seed `42` for data loading and model initialization where the framework
   permits it. Record any source of unavoidable nondeterminism.
4. Keep image size at `224 × 224` for the first experiments. Convert inputs to
   RGB without changing the original materialized files.
5. Compute any class weights from the training split only. They must never use
   validation or protected-test counts.
6. Change one meaningful factor per experiment and record it before the run.

## Planned experiment sequence

| Order | Experiment | Purpose | Selection rule |
| --- | --- | --- | --- |
| V2-E0 | Majority-class baseline | Establish the minimum reference score without training a neural network. | Record validation Macro F1 and accuracy only. |
| V2-E1 | Compact CNN from scratch | Establish a reproducible image-model baseline. | Compare validation Macro F1, per-class recall, and overfitting signals. |
| V2-E2 | Frozen ImageNet-pretrained MobileNetV2 | Test transfer learning at the same `224 × 224` resolution. | Keep only if validation evidence is stronger than V2-E1. |
| V2-E3 | Selective MobileNetV2 fine-tuning | Optional improvement attempt after a stable frozen result. | Run only with a recorded reason; accept only a clear validation improvement without unacceptable regressions. |

For V2-E1, use pixel values scaled to `[0, 1]`. For MobileNetV2 experiments,
use the official MobileNetV2 preprocessing function. The preprocessing method
is part of each experiment record and must be repeated exactly at inference.

## Initial training controls

- Start with batch size `32`; reduce it only if the available hardware runs out
  of memory, and record the change.
- Use categorical cross-entropy with the fixed seven-class mapping.
- Train for at most 20 epochs initially, with early stopping on validation loss
  and patience of 4 epochs.
- Save the best validation checkpoint for each experiment, but do not commit
  model files to Git.
- Do not use random augmentation in validation or protected-test input
  pipelines.

These are initial controls, not invented results. Any changed value must be
recorded as a new experiment rather than silently replacing an earlier run.

## Evaluation and selection

The primary model-selection metric is **validation Macro F1**. It treats the
seven classes equally, which matters because `crack` has many more examples
than classes such as `unpaved_road`.

For each experiment, record:

- validation accuracy and Macro F1;
- per-class precision, recall, and F1;
- a validation confusion matrix;
- training and validation learning curves;
- preprocessing, class weights, seed, epoch count, and key hyperparameters;
- any observed limitations or likely overfitting.

After selecting exactly one candidate from validation evidence, evaluate that
locked candidate once on `protected_test`. Report protected-test Macro F1,
accuracy, per-class metrics, and a confusion matrix. Do not return to tuning
after seeing that result.

## Stop rules and limitations

- Stop and document a run if training improves while validation performance
  repeatedly worsens; this is possible overfitting.
- Do not claim a class label is semantically perfect merely because it came
  from an audited source; source-label limitations remain documented.
- Do not present image-level labels as bounding-box annotations or detection
  performance.
- Keep V1 results and V2 results separate in reports and presentations.

## Next approved-sized task

Create a V2-E0/V2-E1 training notebook or script that performs only the
majority baseline and compact-CNN baseline, writes validation evidence, and
does not load or evaluate `protected_test`.
