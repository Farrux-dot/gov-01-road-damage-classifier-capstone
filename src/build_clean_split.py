"""Build a duplicate-free stratified image split without changing raw data."""
from __future__ import annotations

import argparse
import csv
import hashlib
import random
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image, UnidentifiedImageError

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
LABELS = ("Normal", "Pothole")
SPLIT_RATIOS = {"train": 0.70, "validation": 0.15}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def readable_image(path: Path) -> bool:
    try:
        with Image.open(path) as image:
            image.verify()
        return True
    except (UnidentifiedImageError, OSError):
        return False


def unique_labeled_images(data_dir: Path) -> dict[str, list[tuple[Path, str]]]:
    images: dict[str, list[tuple[Path, str]]] = {label: [] for label in LABELS}
    seen_hashes: set[str] = set()
    for supplied_split in ("train", "val", "valid", "validation"):
        split_dir = data_dir / supplied_split
        if not split_dir.is_dir():
            continue
        for label in LABELS:
            label_dir = split_dir / label
            if not label_dir.is_dir():
                continue
            for image_path in sorted(label_dir.rglob("*")):
                if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                    continue
                if not readable_image(image_path):
                    continue
                digest = sha256(image_path)
                if digest in seen_hashes:
                    continue
                seen_hashes.add(digest)
                images[label].append((image_path, digest))
    if not any(images.values()):
        raise ValueError(f"No readable Normal/Pothole images found below {data_dir}")
    return images


def stratified_split(images: dict[str, list[tuple[Path, str]]], seed: int) -> dict[str, list[tuple[str, Path, str]]]:
    rng = random.Random(seed)
    result: dict[str, list[tuple[str, Path, str]]] = {"train": [], "validation": [], "test": []}
    for label, records in images.items():
        records = records.copy()
        rng.shuffle(records)
        train_end = round(len(records) * SPLIT_RATIOS["train"])
        validation_end = train_end + round(len(records) * SPLIT_RATIOS["validation"])
        for split, partition in (
            ("train", records[:train_end]),
            ("validation", records[train_end:validation_end]),
            ("test", records[validation_end:]),
        ):
            result[split].extend((label, path, digest) for path, digest in partition)
    return result


def write_summary(split_data: dict[str, list[tuple[str, Path, str]]], path: Path, seed: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=("split", "rows", "normal_count", "pothole_count", "pothole_rate", "split_method", "seed", "notes"))
        writer.writeheader()
        for split in ("train", "validation", "test"):
            counts = Counter(label for label, _, _ in split_data[split])
            total = len(split_data[split])
            writer.writerow({
                "split": split,
                "rows": total,
                "normal_count": counts["Normal"],
                "pothole_count": counts["Pothole"],
                "pothole_rate": f"{counts['Pothole'] / total:.6f}",
                "split_method": "stratified exact-hash-deduplicated",
                "seed": seed,
                "notes": "Raw supplied test folder excluded because it overlaps with train/validation.",
            })


def write_issue_log(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "issue_id": "DQ-01",
            "finding": "The supplied flat test folder contains 136 images that overlap with supplied training and/or validation images.",
            "evidence_path": "docs/image_manifest.csv; docs/data_audit.md",
            "risk": "Invalid final evaluation due to test leakage.",
            "decision": "Exclude the supplied test folder.",
            "action_or_limitation": "Use the rebuilt clean test split only.",
            "status": "Resolved in derived clean split",
            "owner": "Student",
        },
        {
            "issue_id": "DQ-02",
            "finding": "Exact duplicate hashes cross the supplied splits.",
            "evidence_path": "docs/image_manifest.csv; docs/split_summary.csv",
            "risk": "Validation and test metrics may be inflated.",
            "decision": "Keep each unique image hash in exactly one derived split.",
            "action_or_limitation": "Run the zero-overlap verification before modeling.",
            "status": "Resolved in derived clean split",
            "owner": "Student",
        },
        {
            "issue_id": "DQ-03",
            "finding": "The unique labeled pool has fewer Normal than Pothole images.",
            "evidence_path": "docs/split_summary.csv; docs/data_audit.md",
            "risk": "Accuracy may hide poor Normal-class performance.",
            "decision": "Preserve class ratios and use macro F1 with class-level precision and recall.",
            "action_or_limitation": "Any augmentation or class weighting will be applied only during training.",
            "status": "Accepted limitation",
            "owner": "Student",
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def copy_split(split_data: dict[str, list[tuple[str, Path, str]]], output_dir: Path) -> None:
    for split, records in split_data.items():
        for label, source, digest in records:
            destination = output_dir / split / label / f"{digest[:12]}_{source.name}"
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)


def verify_zero_overlap(output_dir: Path) -> None:
    seen: dict[str, str] = {}
    for split in ("train", "validation", "test"):
        for image_path in (output_dir / split).rglob("*"):
            if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            digest = sha256(image_path)
            previous_split = seen.get(digest)
            if previous_split and previous_split != split:
                raise RuntimeError(f"Duplicate hash crosses derived splits: {image_path}")
            seen[digest] = split


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--split-summary", type=Path, required=True)
    parser.add_argument("--issue-log", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing output directory: {args.output_dir}")

    images = unique_labeled_images(args.data_dir)
    split_data = stratified_split(images, args.seed)
    copy_split(split_data, args.output_dir)
    verify_zero_overlap(args.output_dir)
    write_summary(split_data, args.split_summary, args.seed)
    write_issue_log(args.issue_log)
    for split in ("train", "validation", "test"):
        print(f"{split}: {Counter(label for label, _, _ in split_data[split])}")
    print(f"Created clean split at {args.output_dir}")


if __name__ == "__main__":
    main()
