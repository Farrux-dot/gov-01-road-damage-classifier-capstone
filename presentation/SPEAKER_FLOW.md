# GOV-01 Speaker Flow

1. “Municipal staff may receive many road photos. My project gives a first `Normal` or `Pothole` classification to support human review.”
2. “It does not decide severity, danger, repair priority, or road safety.”
3. “The supplied folders contained duplicate images, including all supplied test images. I removed exact duplicates and rebuilt a clean 70/15/15 split from 1,228 unique labelled images.”
4. “I compared a naive rule, a compact CNN, a class-weighted CNN, and MobileNetV2. I selected corrected frozen MobileNetV2 V4 using validation Macro F1.”
5. “The locked V4 model achieved Macro F1 0.939901 and accuracy 0.950820 on 183 protected clean test images. No tuning followed that test.”
6. “It missed 7 potholes and made 2 false pothole alerts. Missing a pothole is the more serious risk, so human review is required.”
7. “The local Streamlit app loads the saved model and predicts one image. It does not retrain.”
8. “The source images are low resolution and may not represent every real road condition. Future work is external, diverse evaluation.”

## Demo choreography

1. Open the local Streamlit app.
2. State that the model file was saved after V1 training and stays private.
3. Upload one road image and select **Classify image**.
4. Read the label and probability, then state the human-review boundary.
5. If the app fails, use `FALLBACK_EVIDENCE.md`; do not retrain or alter the final model during the defense.
