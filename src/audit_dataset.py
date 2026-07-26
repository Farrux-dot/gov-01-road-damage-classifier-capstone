"""Audit image-classification data before model training."""
from __future__ import annotations

import argparse
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
    args = parser.parse_args()

    root = args.data_dir
    if not root.exists():
        raise FileNotFoundError(root)

    report: dict[str, object] = {"data_dir": str(root), "splits": {}, "duplicate_files_across_splits": [], "warnings": []}
    hashes: dict[str, list[str]] = {}
    class_sets: list[set[str]] = []

    for split in EXPECTED_SPLITS:
        split_dir = find_split(root, split)
        classes = sorted(path.name for path in split_dir.iterdir() if path.is_dir())
        if len(classes) != 2:
            report["warnings"].append(f"{split}: expected two classes but found {classes}")
        class_sets.append(set(classes))
        counts: Counter[str] = Counter()
        unreadable: list[str] = []
        for class_name in classes:
            for image_path in (split_dir / class_name).rglob("*"):
                if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                    continue
                counts[class_name] += 1
                try:
                    with Image.open(image_path) as image:
                        image.verify()
                except (UnidentifiedImageError, OSError):
                    unreadable.append(str(image_path))
                    continue
                hashes.setdefault(file_digest(image_path), []).append(str(image_path))
        report["splits"][split] = {"path": str(split_dir), "classes": classes, "class_counts": dict(counts), "unreadable_images": unreadable}

    if len({frozenset(items) for items in class_sets}) > 1:
        report["warnings"].append("Class folders are inconsistent across splits.")
    report["duplicate_files_across_splits"] = [paths for paths in hashes.values() if len({Path(item).parts[-3] for item in paths}) > 1]
    if report["duplicate_files_across_splits"]:
        report["warnings"].append("Exact duplicate image files were found across splits; resolve them before training.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
