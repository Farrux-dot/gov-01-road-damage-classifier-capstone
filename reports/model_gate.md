# Model Gate Evidence - GOV-01

## 1. Project task and primary metric

- **Project task:** Binary computer-vision classification.
- **Expected user:** Municipal staff reviewing road-condition reports.
- **Raw input:** One RGB road image.
- **Model output:** `Normal` or `Pothole`, plus a pothole probability.
- **Primary metric:** Validation macro F1.
- **Why this metric matches the project need:** The data has fewer Normal images than Pothole images, so macro F1 gives both classes equal importance.

## 2. Data and split identifiers

- **Data version:** Clean exact-hash-deduplicated image pool, 1,228 labeled images.
- **Split ID / strategy:** `stratified_clean_split_seed42`.
- **Train / validation / protected-test boundaries:** Train 860 images; validation 185 images; test 183 images. The test split is protected for final evaluation only.
- **Leakage-prevention note:** The supplied raw test folder was excluded because it contained exact duplicates of training and validation images.
- **Preprocessing fit boundary:** Random augmentation is training-only; validation and test receive no random augmentation.

## 3. Baseline

- **Naive baseline:** `naive_majority_v1`, which predicts Pothole for every validation image.
- **Simple model baseline:** `cnn_unweighted_v1`, a compact CNN trained from scratch.
- **Baseline validation result:** The CNN achieved Macro F1 `0.673898`, compared with `0.420063` for the naive baseline.
- **Evidence:** `reports/experiment_record.csv`, `reports/cnn_unweighted_v1_learning_curve.png`, and `reports/cnn_unweighted_v1_validation_confusion_matrix.png`.

## 4. Experiment hypotheses

| Run ID | Hypothesis | One changed factor | Stable controls | Validation result | Conclusion |
|---|---|---|---|---|---|
| `naive_majority_v1` | The majority-class rule establishes the minimum reference result. | Naive prediction rule | Split, validation labels, macro F1 | Macro F1 `0.420063`; accuracy `0.724324` | Reference floor established |
| `cnn_unweighted_v1` | A compact CNN can learn road-image patterns beyond the majority rule. | Simple CNN model | Split, seed 42, image size, augmentation, validation metric | Macro F1 `0.673898`; accuracy `0.789189`; ROC-AUC `0.867574` | Beats the naive baseline but is weak on Normal recall |
| `cnn_class_weighted_v2` | Class weights improve Normal recall and Macro F1 without changing the CNN architecture. | Class weights only | Split, seed 42, image size, architecture, augmentation, optimizer, validation metric | Macro F1 `0.775295`; accuracy `0.821622`; Normal recall `0.666667` | Current validation leader; record the Pothole-recall trade-off |
| `mobilenetv2_frozen_v3` | Frozen ImageNet MobileNetV2 improves validation Macro F1 over the class-weighted CNN. | Model family and required ImageNet preprocessing | Split, seed 42, image size, augmentation, class weights, validation metric | Macro F1 `0.915463`; accuracy `0.929730`; ROC-AUC `0.983611` | Selected candidate using validation evidence only |

## 5. Run comparison

- **Tracking method:** Repository-visible `reports/experiment_record.csv`.
- **Same split and metric confirmed:** Yes; the notebook uses the clean split, seed 42, and validation macro F1.
- **Important failed or neutral experiment:** The unweighted CNN has Normal recall `0.352941`, so it misses many Normal images.
- **What this taught:** Class weighting improved Normal recall to `0.666667`; frozen MobileNetV2 then improved Macro F1 to `0.915463` with the same class weights.

## 6. Selected candidate or current blocker

- **Selected run ID:** `mobilenetv2_frozen_v3`.
- **Compared directly with class-weighted CNN:** Yes. Macro F1 improved by `0.140168`, accuracy improved by `0.108108`, and Normal recall improved from `0.666667` to `0.941176`.
- **Decisive trade-off:** MobileNetV2 has the best validation Macro F1, the best class-level recall balance, and the best ROC-AUC. Its total training time was about 233 seconds longer because it ran all 20 epochs.
- **Rejected alternative:** `cnn_class_weighted_v2` was rejected as the final candidate because its validation Macro F1 and Normal recall were lower.
- **Current limitation:** The candidate has only validation evidence; the protected test split remains unused.
- **Next action:** Freeze the selected candidate and evaluate it once on the clean protected test split.

## 7. Protected test status

- **Protected test used for candidate selection or tuning:** No.
- **Candidate locked before final test evaluation:** Yes. `mobilenetv2_frozen_v3` was selected using validation evidence only.
- **Final test access:** Not performed.

## 8. Final evaluation

- Not performed. The test split remains protected.

## 9. Error / failure analysis

- **Unweighted CNN errors:** 33 Normal images were predicted as Pothole; 6 Pothole images were predicted as Normal.
- **Class-weighted CNN errors:** 17 Normal images were predicted as Pothole; 16 Pothole images were predicted as Normal.
- **Frozen MobileNetV2 validation errors:** 3 Normal images were predicted as Pothole; 10 Pothole images were predicted as Normal.
- **Likely cause:** Transfer learning provides stronger reusable visual features than the compact CNN on this modest image dataset.
- **Impact:** MobileNetV2 reduces false reports in both classes compared with the class-weighted CNN, but 10 Pothole images were still missed. The model is triage support only and must retain human review.

## 10. Complete inference artifact

- Not produced yet. The eventual artifact must include the model, image size, preprocessing rule, class names, dependency versions, and loading instructions.

## 11. Reload proof

- Not performed. A fresh Colab/runtime reload check will be required after the final model is saved.

## 12. Limitations

- The model identifies pothole presence only; it does not assess pothole danger, size, severity, or repair priority.
- Source metadata does not identify scenes, locations, or repeated subjects, so near-duplicate scene leakage remains a documented limitation.

## 13. Next action and milestone commit

- **Next evidence-based action:** Evaluate the frozen MobileNetV2 candidate once on the clean protected test split, then save and reload the complete inference artifact.
- **Model Gate status:** YELLOW - candidate selection is complete, but protected evaluation, artifact saving, and fresh-runtime reload proof remain.
- **Milestone commit:** To be created after the notebook structure is checked.
