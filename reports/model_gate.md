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
| `cnn_class_weighted_v2` | Class weights improve Normal recall and Macro F1 without changing the CNN architecture. | Class weights only | Split, seed 42, image size, architecture, augmentation, optimizer, validation metric | Macro F1 `0.775295`; accuracy `0.821622`; Normal recall `0.666667` | Improves over the unweighted CNN; record the Pothole-recall trade-off |
| `mobilenetv2_frozen_v3` | Frozen ImageNet MobileNetV2 experiment. | Invalid preprocessing boundary | Split and class weights | Results recorded but invalid | Random augmentation was applied during validation; do not use for selection |
| `mobilenetv2_frozen_v4` | Corrected frozen MobileNetV2 improves validation Macro F1 with training-only augmentation. | Repair: remove augmentation from model inference path | Split, seed 42, image size, class weights, validation metric | Macro F1 `0.933126`; accuracy `0.945946`; Normal recall `0.921569`; Pothole recall `0.955224` | Valid validation leader; lock as candidate |

## 5. Run comparison

- **Tracking method:** Repository-visible `reports/experiment_record.csv`.
- **Same split and metric confirmed:** Yes; the notebook uses the clean split, seed 42, and validation macro F1.
- **Important failed or neutral experiment:** The unweighted CNN has Normal recall `0.352941`, so it misses many Normal images.
- **What this taught:** The first MobileNetV2 run is invalid because random augmentation reached validation inference. Corrected V4 restricts random augmentation to training data and improves Macro F1 to `0.933126`.

## 6. Selected candidate or current blocker

- **Selected run ID:** `mobilenetv2_frozen_v4`.
- **Selection reason:** It is the best valid validation result: Macro F1 `0.933126`, with strong recall for both Normal (`0.921569`) and Pothole (`0.955224`) classes. Its validation preprocessing is correct: random augmentation is applied to training images only.
- **Candidate-lock rule:** The model architecture, seed, image size, class weights, preprocessing, and decision threshold are now fixed. No further tuning is allowed after test access.

## 7. Protected test status

- **Protected test used for candidate selection or tuning:** No.
- **Candidate locked before final test evaluation:** Yes, `mobilenetv2_frozen_v4` is locked using validation evidence only.
- **Final test access:** Not performed.

## 8. Final evaluation

- Not performed. The test split remains protected.

## 9. Error / failure analysis

- **Unweighted CNN errors:** 33 Normal images were predicted as Pothole; 6 Pothole images were predicted as Normal.
- **Class-weighted CNN errors:** 17 Normal images were predicted as Pothole; 16 Pothole images were predicted as Normal.
- **Corrected frozen MobileNetV2 v4 errors:** 4 Normal images were predicted as Pothole; 6 Pothole images were predicted as Normal.
- **Frozen MobileNetV2 v3 errors:** Not used for decision-making because validation images were randomly augmented in error.
- **Impact:** V4 reduces both kinds of validation error, but six missed potholes show that the model remains triage support only and must retain human review.

## 10. Complete inference artifact

- Not produced yet. The eventual artifact must include the model, image size, preprocessing rule, class names, dependency versions, and loading instructions.

## 11. Reload proof

- Not performed. A fresh Colab/runtime reload check will be required after the final model is saved.

## 12. Limitations

- The model identifies pothole presence only; it does not assess pothole danger, size, severity, or repair priority.
- Source metadata does not identify scenes, locations, or repeated subjects, so near-duplicate scene leakage remains a documented limitation.

## 13. Next action and milestone commit

- **Next evidence-based action:** Evaluate locked `mobilenetv2_frozen_v4` once on the protected clean test split and report the result without further tuning.
- **Model Gate status:** YELLOW - candidate selection is complete and the protected test remains untouched.
- **Milestone commit:** Record candidate selection and validation evidence before the protected test evaluation.
