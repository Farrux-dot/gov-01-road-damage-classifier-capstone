# Responsible AI and Limitations — GOV-01

## Intended use

GOV-01 is an educational binary image classifier. It accepts one road image and returns a preliminary `Normal` or `Pothole` label with a pothole probability. The intended use is to help municipal staff sort incoming road-photo reports for **human review**.

The final V1 model is `mobilenetv2_frozen_v4`. It detects possible pothole presence only.

## What the model must not decide

The model must not be used to decide:

- whether a road is safe or unsafe;
- pothole size, depth, danger, or severity;
- repair cost, repair priority, or maintenance scheduling;
- legal liability, insurance decisions, or emergency dispatch;
- whether a citizen report should be automatically closed.

A high probability is not proof that a pothole exists. A low probability is not proof that the road has no defect.

## Data representativeness and bias risks

The Version 1 dataset contains small `64 x 64` road images from one Kaggle source. It has more pothole images than normal images, and it may not represent all:

- countries, cities, road materials, or road-marking styles;
- daylight, shadows, rain, snow, or night conditions;
- camera devices, distances, viewing angles, and image quality;
- road damage types other than the dataset's labelled `Normal` and `Pothole` classes.

The original supplied dataset folders also contained exact duplicates. The project rebuilt a duplicate-free, stratified clean split and verified zero exact-hash overlap. However, no scene, location, or repeated-subject metadata was available, so exact hashes cannot prove that visually similar scenes never cross the splits.

## Error, safety, and misuse risks

On the protected V1 test, the final model missed 7 potholes and produced 2 false pothole alerts. A missed pothole can be harmful if a staff member treats `Normal` as permission to ignore a report. A false alert can waste reviewer time if it is treated as a confirmed defect.

The system can also be misused if someone uploads images that contain people, vehicles, addresses, licence plates, or other identifying information. This project does not need such information for classification and does not provide a system for storing or sharing it.

## Required human oversight

A qualified human must review the original image and any available report context before acting. The reviewer should be especially careful when:

- the image is blurred, dark, distant, or poorly framed;
- the scene differs from the dataset conditions;
- the model predicts `Normal` but the report raises a concern;
- a decision would affect safety, spending, maintenance priority, or public communication.

The Streamlit demo therefore describes a pothole prediction as a **potential pothole** and requires human review. A `Normal` result also states that human review remains required.

## Privacy and security practices

- Raw dataset images, archives, and the private saved `.keras` artifact are not committed to GitHub.
- No API keys, passwords, or secrets are stored in the repository.
- Do not upload or publish road photos containing personal information without permission and an appropriate privacy review.
- For a real municipal deployment, access control, retention rules, consent, and security review would be required.

## Model and data acknowledgements

- Dataset source and download instructions: `data/README.md`.
- Dataset audit and duplicate-removal decision: `docs/data_audit.md`.
- Transfer-learning base: ImageNet-pretrained MobileNetV2, documented in the model notebooks and `artifacts/README.md`.
- Software: TensorFlow/Keras, Streamlit, NumPy, Pillow, scikit-learn, and other packages in `requirements.txt`.

## Future improvement, not a current claim

Future work could collect higher-resolution, geographically diverse images, label difficult negative cases such as shadows and repairs, perform error-slice analysis, and validate on a genuinely external dataset. These are proposed improvements only; they are not evidence that the current V1 model already handles those conditions.
