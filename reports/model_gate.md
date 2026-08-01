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

## 5. Run comparison

- **Tracking method:** Repository-visible `reports/experiment_record.csv`.
- **Same split and metric confirmed:** Yes; the notebook uses the clean split, seed 42, and validation macro F1.
- **Important failed or neutral experiment:** The unweighted CNN has Normal recall `0.352941`, so it misses many Normal images.
- **What this taught:** A class-weighted CNN is the next justified experiment; only the training loss weighting should change.

## 6. Selected candidate or current blocker

- **Selected run ID:** `cnn_unweighted_v1` is the current baseline leader only; it is not the final candidate.
- **Compared directly with baseline:** Yes. Macro F1 improved by `0.253835` over the naive baseline.
- **Current limitation:** Normal recall is only `0.352941` (18 of 51 Normal validation images).
- **Next action:** Run a class-weighted CNN experiment on the same training and validation split.

## 7. Protected test status

- **Protected test used for candidate selection or tuning:** No.
- **Candidate locked before final test evaluation:** Not yet; no candidate has been selected.
- **Final test access:** Not performed.

## 8. Final evaluation

- Not performed. The test split remains protected.

## 9. Error / failure analysis

- **Validation error evidence:** 33 Normal images were predicted as Pothole; 6 Pothole images were predicted as Normal.
- **Likely cause:** The training data contains more Pothole images than Normal images.
- **Impact:** The system would send many Normal-road reports for unnecessary pothole review. The model is triage support only and must retain human review.

## 10. Complete inference artifact

- Not produced yet. The eventual artifact must include the model, image size, preprocessing rule, class names, dependency versions, and loading instructions.

## 11. Reload proof

- Not performed. A fresh Colab/runtime reload check will be required after the final model is saved.

## 12. Limitations

- The model identifies pothole presence only; it does not assess pothole danger, size, severity, or repair priority.
- Source metadata does not identify scenes, locations, or repeated subjects, so near-duplicate scene leakage remains a documented limitation.

## 13. Next action and milestone commit

- **Next evidence-based action:** Implement and run the class-weighted CNN experiment on the same validation protocol.
- **Model Gate status:** YELLOW - baseline evidence is complete, but a fairer Normal-class result and further controlled comparison are required.
- **Milestone commit:** To be created after the notebook structure is checked.
