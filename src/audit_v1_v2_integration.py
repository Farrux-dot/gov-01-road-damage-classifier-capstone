"""Audit whether the V1 clean training split can later supplement V2 data.

This tool reads V1 and SVRDD images only. It does not copy, merge, relabel, or
train on any image. V1 validation and protected-test folders are recorded as
reserved and are not candidates for V2 integration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError


V1_CLASS_TO_V2_STATUS = {
    "Normal": "needs_visual_review_for_normal_asphalt",
    "Pothole": "pothole",
}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
SVRDD_SPLITS = ("train", "validation", "test")


def file_digest(path: Path) -> str:
    """Return an exact SHA-256 content digest."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def image_files(folder: Path) -> list[Path]:
    """Return supported image files in a stable order."""
    return sorted(path for path in folder.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)


def audit_v1_training_split(v1_train_dir: Path) -> tuple[dict[str, Any], dict[str, list[str]]]:
    """Audit V1 training images and retain hashes for a cross-source comparison."""
    class_folders = {path.name: path for path in v1_train_dir.iterdir() if path.is_dir()} if v1_train_dir.is_dir() else {}
    if set(class_folders) != set(V1_CLASS_TO_V2_STATUS):
        raise ValueError(f"Expected V1 classes {sorted(V1_CLASS_TO_V2_STATUS)}, found {sorted(class_folders)}")

    hashes: dict[str, list[str]] = defaultdict(list)
    class_counts: Counter[str] = Counter()
    resolution_counts: Counter[str] = Counter()
    unreadable: list[str] = []
    for class_name, folder in sorted(class_folders.items()):
        for image_path in image_files(folder):
            relative_path = image_path.relative_to(v1_train_dir).as_posix()
            try:
                with Image.open(image_path) as image:
                    image.verify()
                with Image.open(image_path) as image:
                    width, height = image.size
            except (UnidentifiedImageError, OSError):
                unreadable.append(relative_path)
                continue
            class_counts[class_name] += 1
            resolution_counts[f"{width}x{height}"] += 1
            hashes[file_digest(image_path)].append(relative_path)

    duplicate_groups = [items for items in hashes.values() if len(items) > 1]
    return (
        {
            "eligible_v1_split": "train",
            "class_counts": dict(sorted(class_counts.items())),
            "resolution_counts": dict(sorted(resolution_counts.items())),
            "unreadable_image_count": len(unreadable),
            "exact_duplicate_group_count_within_v1_train": len(duplicate_groups),
            "examples": {"unreadable": unreadable[:10], "duplicate_groups": duplicate_groups[:10]},
        },
        hashes,
    )


def audit_cross_source_duplicates(v1_hashes: dict[str, list[str]], svrdd_dir: Path) -> list[dict[str, list[str]]]:
    """Find exact byte-identical images between eligible V1 training and SVRDD."""
    matches: list[dict[str, list[str]]] = []
    for split in SVRDD_SPLITS:
        split_dir = svrdd_dir / split
        if not split_dir.is_dir():
            raise FileNotFoundError(f"Missing SVRDD extracted split: {split}")
        for image_path in image_files(split_dir):
            digest = file_digest(image_path)
            if digest in v1_hashes:
                matches.append(
                    {
                        "v1_train_paths": v1_hashes[digest],
                        "svrdd_paths": [f"{split}/{image_path.relative_to(split_dir).as_posix()}"],
                    }
                )
    return matches


def count_split_images(split_dir: Path) -> dict[str, int]:
    """Count V1 images by class for a reserved split without treating it as eligible."""
    return {folder.name: len(image_files(folder)) for folder in sorted(split_dir.iterdir()) if folder.is_dir()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v1-clean-split", type=Path, required=True, help="V1 data/processed/clean_split folder.")
    parser.add_argument("--svrdd-extracted-dir", type=Path, required=True, help="SVRDD extracted folder containing source splits.")
    parser.add_argument("--output", type=Path, required=True, help="Ignored JSON audit-report path.")
    args = parser.parse_args()

    v1_train_dir = args.v1_clean_split / "train"
    v1_audit, v1_hashes = audit_v1_training_split(v1_train_dir)
    reserved_counts: dict[str, dict[str, int]] = {}
    for split in ("validation", "test"):
        split_dir = args.v1_clean_split / split
        if not split_dir.is_dir():
            raise FileNotFoundError(f"Missing V1 reserved split: {split}")
        reserved_counts[split] = count_split_images(split_dir)

    cross_source_matches = audit_cross_source_duplicates(v1_hashes, args.svrdd_extracted_dir)
    report = {
        "scope": "V1-to-V2 integration readiness; no data is merged by this audit",
        "v1_label_to_v2_status": V1_CLASS_TO_V2_STATUS,
        "eligible_for_future_v2_review": v1_audit,
        "reserved_v1_splits_not_eligible_for_v2_integration": reserved_counts,
        "cross_source_exact_duplicate_group_count": len(cross_source_matches),
        "cross_source_exact_duplicate_examples": cross_source_matches[:25],
        "integration_decision": (
            "needs_normal_visual_review" if not v1_audit["unreadable_image_count"] and not cross_source_matches else "blocked"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Audited {sum(v1_audit['class_counts'].values())} eligible V1 training images")
    print(f"Cross-source exact duplicate groups: {len(cross_source_matches)}")
    print(f"Saved integration report: {args.output}")


if __name__ == "__main__":
    main()
