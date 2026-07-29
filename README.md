# GOV-01 Road Damage Image Classifier

This AI/ML capstone project uses binary image classification to identify the **presence of a pothole** in a submitted road image (`Normal` or `Pothole`). It supports report triage only. It does **not** assess pothole danger, physical size, road safety, repair cost, or repair priority.

## Dataset

## Source

[Kaggle Pothole Detection Dataset](https://www.kaggle.com/datasets/abhinavkulshreshth/pothole-detection-dataset) by `abhinavkulshreshth` (listed on Kaggle as CC0). The downloaded archive contains 1,401 JPEG images; the final project will use the 1,228 unique labeled images identified by the Data Audit.

## Download instructions

1. Open the dataset link above and sign in to Kaggle if prompted.
2. Select **Download** to save the dataset ZIP file.
3. Extract the archive into `data/raw/` in this repository.
4. The downloaded archive is stored under `data/raw/Dataset/`. Its supplied splits are not model-ready because exact duplicates cross the splits.
5. The project will rebuild a clean stratified 70%/15%/15% train/validation/test split from the 1,228 unique labeled images. The supplied flat `test/` folder will not be used because its images overlap with training and validation data.

The downloaded dataset is not committed to this repository.
