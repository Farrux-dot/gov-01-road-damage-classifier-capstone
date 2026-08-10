# GOV-01 Defense Deck Map

Use this evidence-first story. Do not organize the defense by notebook order.

| Block | Main message | Repository evidence | Suggested slide |
|---|---|---|---:|
| Problem and objective | The system predicts `Normal` or `Pothole` to support municipal human review. | `PROJECT_BRIEF.md`; `README.md` | 1 |
| Data and risk | Supplied folders contained duplicate leakage; a clean duplicate-free split was built. | `docs/data_audit.md`; `docs/split_summary.csv` | 2 |
| Pipeline | Image -> RGB resize -> MobileNetV2 preprocessing -> V1 model -> probability -> human review. | `docs/preprocessing_manifest.json`; `src/inference.py` | 3 |
| Experiments and selection | V4 was selected after baseline and controlled validation comparison. | `reports/experiment_record.csv`; `reports/model_gate.md` | 4 |
| Evaluation and errors | Protected Macro F1 `0.939901`; 7 missed potholes and 2 false alerts. | `reports/error_analysis/ERROR_ANALYSIS.md` | 5 |
| Demo | Local Streamlit loads the saved artifact without training. | `app.py`; `docs/REPRODUCTION_TEST.md` | 6 |
| Limitations | Human review is required; no severity or safety decision. | `docs/RESPONSIBLE_AI_AND_LIMITATIONS.md` | 7 |
| Conclusion | V1 is final; future work is diverse external evaluation, not post-test tuning. | `RUBRIC_EVIDENCE_MATRIX.md` | 8 |

## One-sentence conclusion

`mobilenetv2_frozen_v4` is a reproducible, high-performing model on this project's clean held-out split, but it remains an educational human-review triage tool with limits on real-world generalization.
