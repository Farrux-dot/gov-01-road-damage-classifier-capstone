"""Audit image-classification data before model training."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image, UnidentifiedImageError

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
EXPECTED_SPLITS = ("train", "val", "test")


def find_split(root: Path, split: str) -> Path:
    matches = [path for path in root.iterdir() if path.is_dir() and path.name.lower() in {split, "valid" if split == "val" else split, "validation" if split == "val" else split}]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one '{split}' split under {root}; found: {matches}")
    return matches[0]


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, help="Optional CSV manifest for every readable image.")
    args = parser.parse_args()

    root = args.data_dir
    if not root.exists():
        raise FileNotFoundError(root)

    report: dict[str, object] = {"data_dir": str(root), "splits": {}, "duplicate_files_across_splits": [], "warnings": []}
    hashes: dict[str, list[dict[str, str]]] = {}
    class_sets: list[set[str]] = []
    manifest_rows: list[dict[str, str]] = []

    for split in EXPECTED_SPLITS:
        split_dir = find_split(root, split)
        classes = sorted(path.name for path in split_dir.iterdir() if path.is_dir())
        if len(classes) != 2:
            report["warnings"].append(f"{split}: expected two classes but found {classes}")
        class_sets.append(set(classes))
        counts: Counter[str] = Counter()
        unreadable: list[str] = []
        image_groups = [(class_name, split_dir / class_name) for class_name in classes]
        if not image_groups:
            image_groups = [("", split_dir)]
        for class_name, image_root in image_groups:
            for image_path in image_root.rglob("*"):
                if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                    continue
                if class_name:
                    counts[class_name] += 1
                try:
                    with Image.open(image_path) as image:
                        image.verify()
                except (UnidentifiedImageError, OSError):
                    unreadable.append(str(image_path))
                    continue
                digest = file_digest(image_path)
                row = {
                    "filepath": image_path.as_posix(),
                    "split": split,
                    "label": class_name or "unknown",
                    "label_source": "class_folder" if class_name else "unverified_filename_prefix",
                    "group_id": "unknown",
                    "sha256": digest,
                }
                manifest_rows.append(row)
                hashes.setdefault(digest, []).append(row)
        report["splits"][split] = {"path": str(split_dir), "classes": classes, "class_counts": dict(counts), "unreadable_images": unreadable}

    if len({frozenset(items) for items in class_sets}) > 1:
        report["warnings"].append("Class folders are inconsistent across splits.")
    report["duplicate_files_across_splits"] = [
        [item["filepath"] for item in items]
        for items in hashes.values()
        if len({item["split"] for item in items}) > 1
    ]
    if report["duplicate_files_across_splits"]:
        report["warnings"].append("Exact duplicate image files were found across splits; resolve them before training.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.manifest_output:
        args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
        with args.manifest_output.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=("filepath", "split", "label", "label_source", "group_id", "sha256"))
            writer.writeheader()
            writer.writerows(manifest_rows)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
