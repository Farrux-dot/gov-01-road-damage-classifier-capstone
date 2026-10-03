# GOV-01 V2 Multi-label final result

## Decision

`E7` is the final V2 multi-label model. It was selected before the protected test from validation evidence, then reported once on the untouched expansion test. The older historic E2 split was not used for this decision because the later expansion split redistributed images and would not have been unseen for both historic models.

## Final protected-test evidence

The final report compared the locked E6 baseline and locked E7 candidate on the same 3,978-image N-RDD expansion protected test. Both models used thresholds selected earlier on validation data. The test was not used for training, threshold calibration, or another experiment.

| Model | Masked macro F1 | Masked label accuracy |
|---|---:|---:|
| E6 baseline | 87.09% | 90.39% |
| **E7 final model** | **88.17%** | **91.13%** |

`Masked` means a condition was scored only when the source label was known. This prevents missing labels from being treated as negative labels.

## Per-condition F1

| Condition | E6 | E7 |
|---|---:|---:|
| Crack | 92.69% | **93.21%** |
| Pothole | 68.44% | **71.28%** |
| Repaired road | 85.55% | **87.72%** |
| Manhole cover | 65.26% | **66.77%** |
| Unpaved road | 98.15% | **98.88%** |
| Road marking | **99.57%** | 99.35% |
| Speed bump | 100.00% | 100.00% |

## Operational interpretation

- E7 detected 402 of 557 known potholes, 29 more than E6, while producing 9 more pothole false alarms.
- E7 detected the same number of known manhole covers as E6 (418 of 647) while reducing false alarms from 216 to 187.
- E7 is therefore the stronger practical option for the two difficult road conditions while also improving overall macro F1.
- A speed-bump F1 of 100% comes from only 123 known positive test examples. It must not be interpreted as perfect real-world performance.

## Using the locked model

The tracked [E7 configuration](../artifacts/v2_multilabel_e7_config.json) contains the final 320×320 input rule and the seven thresholds. The private `e7_focused_best.keras` file must be extracted from the E7 output ZIP and kept outside Git. Run one local prediction with:

```powershell
python -m src.v2_multilabel_e7_inference `
  --model-path artifacts/e7_focused_best.keras `
  --image C:/path/to/new_road_image.jpg
```

The script returns every condition score and whether it meets its locked threshold. It does not train, calibrate, or change the model.

## Limits

The result supports road-report triage only. A qualified human must confirm every detected condition. The model does not determine defect severity, danger, repair priority, repair cost, or road safety. Test data must not be reused to tune E7.
