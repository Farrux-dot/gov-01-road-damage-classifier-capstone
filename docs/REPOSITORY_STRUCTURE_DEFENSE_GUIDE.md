# GOV-01 Repository Structure - Defense Guide

## The one idea to remember

This repository tells one evidence-based story:

```text
Road images -> data audit -> clean split -> model experiments -> protected test
-> saved V1 model -> Streamlit prediction -> human review
```

Do not try to explain every file during the defense. Start with the user problem, then open only the file that proves the claim you are making.

## Top-level map

```text
gov-01-road-damage-classifier-capstone/
|
|-- data/           Dataset source instructions; raw images stay out of Git
|-- docs/           Data audit, preprocessing, reproducibility, and defense documents
|-- notebooks/      Colab training and modeling workflow
|-- reports/        Experiment metrics, curves, confusion matrices, error analysis
|-- artifacts/      Final-model configuration and reload proof; local .keras model is ignored
|-- src/            Reusable Python code for audit, split, training, evaluation, and inference
|-- tests/          Small automated checks for inference and Git hygiene
|-- presentation/   Final defense deck, speaker notes, Q&A, and fallback evidence
|
|-- app.py          Streamlit user interface
|-- smoke_test.py   Quick local saved-model check
|-- README.md       Main guide for a reviewer
|-- PROJECT_BRIEF.md
|-- PROJECT_STATUS.md
|-- RUBRIC_EVIDENCE_MATRIX.md
|-- requirements.txt
|-- index.html      Static project showcase for GitHub Pages
```

## Start here during a defense

| If the instructor asks about... | Open this first | What to say in simple language |
|---|---|---|
| The problem, user, ML task, and scope | `PROJECT_BRIEF.md` | "Municipal staff upload one road image. The model returns `Normal` or `Pothole` to support human review, not to make repair or safety decisions." |
| Quick project overview | `README.md` | "This is the main reviewer guide. It links to the final result, evidence, local/public demo instructions, and data documentation." |
| Why the data was changed | `docs/data_audit.md` | "The supplied folders had duplicate images, including a duplicate supplied test set, so I built a clean split before training." |
| Which model won and why | `reports/model_gate.md` | "V4 was the best valid validation candidate. I did not choose it from the protected test." |
| Final performance and errors | `reports/model_gate.md` and `reports/error_analysis/ERROR_ANALYSIS.md` | "The protected-test Macro F1 was 0.939901. It missed 7 potholes and made 2 false alerts, so a person must review results." |
| How the app works | `app.py` and `src/inference.py` | "The app loads a saved model and config, prepares one image, predicts, and shows the result. It does not train." |
| Limitations and safety | `docs/RESPONSIBLE_AI_AND_LIMITATIONS.md` | "It detects possible pothole presence only. It cannot decide severity, safety, size, or repair priority." |

## Root files

### `README.md` - the front door

This is the first file a reviewer should read. It states the project scope, final V1 result, links to final evidence, explains how to run the app, and shows the high-level repository structure.

**Defense sentence:** "The README is my starting point for a reviewer. It links directly to the final model gate, error analysis, reproducibility test, and defense materials."

### `PROJECT_BRIEF.md` - the original project contract

This explains the real-world problem, intended user, machine-learning formulation, data plan, planned experiments, success criteria, and risk boundaries. It proves that the final project stayed aligned with GOV-01.

**Important scope:** The model predicts pothole presence only. It is not a safety, severity, or repair-priority system.

### `PROJECT_STATUS.md` - current readiness state

This records the selected final candidate, protected-test result, V2 boundary, working demo routes, completed evidence, and remaining personal defense tasks. It is a status summary, not a source of new model metrics.

### `RUBRIC_EVIDENCE_MATRIX.md` - the grading map

This maps each official rubric criterion to concrete project evidence. Use it when an instructor asks, "Where is the evidence for Criterion 4?" or "How is the project reproducible?"

### `requirements.txt` - needed Python libraries

This lists the Python packages needed to run the app and supporting code. It keeps setup reproducible. It does not contain model weights or secrets.

### `index.html` - public showcase

This is the single static page published through GitHub Pages. It introduces the project and links to the live Streamlit demo. It is not the prediction model itself.

### `.gitignore` - what must not be uploaded

This file tells Git not to upload private, large, or generated files such as raw images, processed images, saved `.keras` model files, virtual environments, caches, and temporary folders.

**Defense sentence:** "The raw data and local model file are intentionally excluded from Git to avoid uploading large external data or private local artifacts. The repository keeps the documentation and configuration needed to understand and reproduce the workflow."

## `data/` - where the data came from

`data/README.md` is the data guide. It documents the Kaggle source, licence status to recheck, download steps, original dataset size, derived clean split, class imbalance, duplicates, and limitations.

Raw images belong in `data/raw/`, but are ignored by Git. This keeps the public repository small and avoids republishing externally sourced images.

Key facts to remember:

- Original archive: 1,401 images.
- Clean unique labelled pool: 1,228 images.
- Classes: 337 `Normal`, 891 `Pothole`.
- Clean split: 860 train, 185 validation, 183 protected test.
- The supplied test folder was excluded because all 136 images duplicated training and/or validation images.

## `docs/` - evidence and documentation

| File | Role in the project | When to use it in defense |
|---|---|---|
| `data_audit.md` | Records image integrity, duplicate leakage, class imbalance, clean-split decision, and preprocessing boundary. | To explain why you did not trust the original supplied test folder. |
| `image_manifest.csv` | Row-by-row audit record of readable source images and hashes. | Supporting technical proof; do not open unless asked for detailed audit evidence. |
| `clean_image_manifest.csv` | Row-by-row record of the final clean split. | To support the zero-exact-overlap claim. |
| `split_summary.csv` | Compact count table for the train, validation, and test split. | To show split sizes and class counts quickly. |
| `issue_log.csv` | Tracks the data problems found, their risks, and decisions. | To show that duplicate leakage was handled deliberately. |
| `preprocessing_manifest.json` | Machine-readable record of image size, preprocessing, augmentation, seed, and split boundary. | To explain the preprocessing contract. |
| `modeling_readiness.md` | Historical plan written before modelling. | Use it only to show the planned safeguards. Final model claims must come from `reports/model_gate.md`. |
| `REPRODUCTION_TEST.md` | Records the verified local setup, model load, tests, Streamlit run, and one visible prediction. | To answer "Can another person run this?" |
| `RESPONSIBLE_AI_AND_LIMITATIONS.md` | Defines intended use, prohibited decisions, data risks, privacy concerns, false-negative risk, and human oversight. | To answer Responsible AI questions. |
| `AI_DEBUG_REPORT.md` | Documents a small repository-safety fix and its automated tests. | Optional technical evidence; only open if asked about quality checks. |
| `defense_pitch_outline.md` | Your five-minute defense route and public demo route. | Use as your practice script, not something to read word-for-word. |
| `capstone_evidence_matrix.md` | EXTC4 matrix covering all eight criteria and three passed locator checks. | Use this as the final defense checklist. |
| `defense_question_bank.md` | Short answers to likely questions, with evidence paths and limitations. | Use for personal practice before defense. |
| `final_action_plan.md` | Records remaining personal preparation tasks. | Use before submission to see what is still not complete. |

## `notebooks/` - the Colab modelling history

These are the notebooks used to prepare and compare models. They are evidence of the workflow, but you do not need to run all of them during the defense.

| Notebook | Purpose |
|---|---|
| `GOV_01_data_preprocessing.ipynb` | Loads the clean split, verifies the folders, and applies augmentation only to training images. |
| `GOV_01_class_weighted_cnn.ipynb` | Tests a compact CNN with class weights as one improvement experiment. |
| `GOV_01_mobilenetv2_transfer.ipynb` | Early MobileNetV2 transfer-learning work. The V3 result is not valid for selection because augmentation reached validation inference. |
| `GOV_01_mobilenetv2_transfer_v4.ipynb` | Corrected frozen MobileNetV2 V4 workflow. This produced the selected final V1 candidate. |
| `GOV_01_model_gate.ipynb` | Collects final evaluation, reload proof, and model-gate evidence. |

**Important defense point:** The notebooks are historical evidence. The final decision is summarized in `reports/model_gate.md`, so use that file first when discussing final results.

## `src/` - reusable Python code

The notebooks are for experiments; `src/` contains reusable scripts and functions.

| File | What it does | Simple explanation |
|---|---|---|
| `audit_dataset.py` | Checks image folders, class folders, readable images, SHA-256 hashes, and cross-split duplicates. | "It inspects the original data before modelling so I can find broken files and leakage." |
| `build_clean_split.py` | Removes exact duplicate hashes, creates a reproducible stratified split with seed 42, copies clean images, and verifies no exact overlap. | "It created the clean train/validation/test split without changing the raw download." |
| `train.py` | Provides generic baseline-CNN or MobileNetV2 training code. | "It is a reusable training script; the final documented experiments are in the notebooks and model gate." |
| `evaluate.py` | Calculates test metrics, writes predictions, and saves a confusion matrix for a saved model. | "It is a reusable evaluation script. The official final result is the protected-test record in `reports/model_gate.md`." |
| `inference.py` | Loads the model configuration and model, validates/changes uploaded images to RGB, resizes them, applies the locked threshold, and returns the prediction. | "This is the reliable prediction engine used by the app." |
| `predict.py` | A simple command-line single-image prediction script. | "It is an alternative command-line inference route; the Streamlit app uses `inference.py` for its user-facing flow." |
| `__init__.py` | Marks `src` as a reusable Python package. | "It allows other project files and tests to import the shared code." |

## `reports/` - model evidence

This is the most important folder for modelling and evaluation questions.

| File group | Purpose |
|---|---|
| `experiment_record.csv` | One-line comparison of the naive rule, compact CNN, class-weighted CNN, invalid V3, and valid V4. |
| `model_gate.md` | The final selection document: task, clean split, baselines, experiments, V4 selection, protected test, errors, reload proof, and limitations. This is the best file for final-result questions. |
| `*_learning_curve.png` | Training and validation loss evidence for each recorded model run. |
| `*_validation_confusion_matrix.png` | Validation prediction errors for each run. |
| `mobilenetv2_frozen_v4_protected_test_confusion_matrix.png` | Final protected-test error counts for the selected V1 model. |
| `mobilenetv2_frozen_v4_reload_proof.png` | Visual proof that the saved model gave the same prediction in a fresh Colab runtime. |
| `error_analysis/ERROR_ANALYSIS.md` | Explains the 7 missed potholes, 2 false alerts, generalization limits, and required human oversight. |

Remember these figures:

- Naive validation Macro F1: `0.420063`.
- Simple CNN validation Macro F1: `0.673898`.
- Selected V4 validation Macro F1: `0.933126`.
- Final protected-test Macro F1: `0.939901`.
- Final protected-test accuracy: `0.950820`.
- Final protected test: 183 images; 7 missed potholes; 2 false pothole alerts.

## `artifacts/` and `models/` - saved-model area

`artifacts/` describes the selected model used for inference:

- `mobilenetv2_frozen_v4_config.json` is tracked. It records classes, RGB `224 x 224` input, MobileNetV2 preprocessing, the `0.5` decision threshold, seed, and final metrics.
- `reload_proof.md` records that the same known image produced probability `0.907272` before and after loading the saved model in a fresh Colab runtime.
- `mobilenetv2_frozen_v4.keras` is the final binary model file, but it is intentionally ignored by Git.

`models/` is the normal destination for generated training-model files. It contains `.gitkeep` only in the public repository because generated `.keras` files are excluded.

**Important:** The public Streamlit deployment downloads the final model from the public Hugging Face model repository. The app can also use a private local copy in `artifacts/`.

## `tests/` and `smoke_test.py` - reliability checks

| File | What it proves |
|---|---|
| `tests/test_inference.py` | Uploaded images convert to RGB and resize correctly; the locked threshold is used; invalid model probabilities are rejected. It uses a tiny fake model, not the protected test data. |
| `tests/test_repository_hygiene.py` | Virtual-environment folders are ignored by Git, so they are not accidentally uploaded. |
| `smoke_test.py` | With a private saved model and one local image, checks that the model loads and produces a valid prediction. It does not train or evaluate the model. |

## `presentation/` - final-defense material

| File | Purpose |
|---|---|
| `GOV_01_Road_Damage_Classifier_Defense.pptx` | Your final eight-slide defense deck. |
| `DEFENSE_DECK_MAP.md` | Connects each slide to its key repository evidence. |
| `SPEAKER_FLOW.md` | Short speaking reminders for the project story. |
| `Q_AND_A_BANK.md` | Existing question-and-answer practice bank. |
| `FALLBACK_EVIDENCE.md` | What to show if the live demo is temporarily unavailable. |
| `fallback_evidence/` | Real screenshots of local model loading, automated tests, and a Streamlit prediction. They are backup proof, not new evaluation metrics. |

## Three things you must not say

1. Do not say the model determines road safety, pothole severity, repair priority, size, danger, or repair cost.
2. Do not say the supplied original test folder was used for final evaluation. It was excluded because of duplicate leakage.
3. Do not present V2 or the MobileNetV2 V3 result as the final model. The final assessed candidate is **V1 `mobilenetv2_frozen_v4`**.

## The shortest possible defense navigation route

If you have only one minute to show the repository:

1. Open `README.md` - overview and final result.
2. Open `docs/data_audit.md` - why the clean split was necessary.
3. Open `reports/model_gate.md` - experiment comparison and protected test.
4. Open `reports/error_analysis/ERROR_ANALYSIS.md` - honest mistakes and limits.
5. Open the public Streamlit app - one image -> result.
6. Open `docs/RESPONSIBLE_AI_AND_LIMITATIONS.md` - human-review boundary.

This route proves the full story without a long code tour.
