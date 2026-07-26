# GOV-01: Road Damage Image Classifier

An individual AI/ML Fundamentals capstone project for municipal road-report triage. The model classifies a submitted road image as **Normal** or **Pothole**. It is decision support only; it is not an engineering safety assessment.

## Project scope

- **Scenario:** GOV-01 - Road Damage Image Classification
- **ML task:** binary image classification
- **Input:** a JPG, JPEG, or PNG road image
- **Output:** predicted class and confidence score
- **Primary metric:** macro F1 score on a held-out test set
- **Dataset:** Kaggle Pothole Detection Dataset (`abhinavkulshreshth/pothole-detection-dataset`), listed by Kaggle as CC0. Record the access date and retain the dataset page link in the final report.

## Repository layout

```text
data/                 # Downloaded dataset (not committed)
models/               # Saved model artifacts (not committed)
reports/              # Audit, metrics, plots and error-analysis outputs
src/                  # Audit, training, evaluation and prediction code
notebooks/            # Colab-first reproducible demo
```

## Setup

1. Clone or download this repository.
2. Create an environment and install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Download the selected Kaggle dataset manually and place its contents under `data/raw/`.
4. Make sure the data exposes three splits, each containing `Normal` and `Pothole` image folders. If the downloaded folder names differ, pass the appropriate `--data-dir` path.
5. Run the audit before training:

   ```bash
   python src/audit_dataset.py --data-dir data/raw --output reports/dataset_audit.json
   ```

6. Train the baseline and transfer-learning models:

   ```bash
   python src/train.py --data-dir data/raw --model baseline_cnn
   python src/train.py --data-dir data/raw --model mobilenetv2
   ```

7. Evaluate the chosen final model and create an error-analysis report:

   ```bash
   python src/evaluate.py --data-dir data/raw --model-path models/mobilenetv2.keras
   ```

8. Run a prediction:

   ```bash
   python src/predict.py --model-path models/mobilenetv2.keras --image path/to/road.jpg
   ```

## Required capstone evidence

Before submission, add the actual audit results, experiment table, test metrics, confusion matrix, error-analysis examples, final model justification, and responsible-AI discussion. Never invent numbers or screenshots.

## Limitations and responsible use

This prototype can be affected by lighting, shadows, weather, camera angle, image blur, pavement texture, and road conditions that differ from the training data. It must not be used as an automatic safety decision or a replacement for human inspection. Images may include location-identifying details; avoid uploading private or sensitive images to public services.
