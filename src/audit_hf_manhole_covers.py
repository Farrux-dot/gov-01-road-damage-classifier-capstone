"""Audit the approved Hugging Face manhole-cover image dataset.

The source is image-level classification data. This audit preserves its
official train/valid/test boundaries and does not create boxes, a V2 split, or
model-training data. Only source-train images labelled ``manhole`` can become
pre-split V2 lookalike candidates.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from PIL import Image


SOURCE_ID = "delima87_manhole_covers_dataset"
SOURCE_URL = "https://huggingface.co/datasets/delima87/manhole_covers_dataset"
SOURCE_LICENSE = "Apache-2.0 stated on the dataset card; recheck before redistribution"
SPLITS = ("train", "valid", "test")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
FIELDNAMES = (
    "source_record_id", "source_split", "source_label", "relative_image_path",
    "sha256", "width", "height", "exact_duplicate_group_id", "candidate_status",
    "candidate_reason",
)


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def relative(path: Path, project_root: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def source_image_directories(data_dir: Path) -> list[tuple[str, str, Path]]:
    directories: list[tuple[str, str, Path]] = []
    for split in SPLITS:
        split_dir = data_dir / split / split
        if not split_dir.is_dir():
            raise FileNotFoundError(f"Expected extracted source split folder: {split_dir}")
        labels = sorted(path for path in split_dir.iterdir() if path.is_dir())
        if {path.name for path in labels} != {"manhole", "void"}:
            raise ValueError(f"{split} labels must be manhole and void, found {[path.name for path in labels]}")
        directories.extend((split, label.name, label) for label in labels)
    return directories


def audit_dataset(data_dir: Path, project_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    hashes: dict[str, list[int]] = defaultdict(list)
    for split, label, directory in source_image_directories(data_dir):
        for image_path in sorted(path for path in directory.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES):
            with Image.open(image_path) as image:
                image.verify()
            with Image.open(image_path) as image:
                width, height = image.size
            status = "source_train_manhole_candidate" if split == "train" and label == "manhole" else "reserved_not_v2_candidate"
            reason = (
                "source train image labelled manhole; image-level candidate only, no boxes"
                if status == "source_train_manhole_candidate"
                else "source void label or official validation/test split is not a V2 candidate"
            )
            row = {
                "source_record_id": f"{split}::{label}::{image_path.name}",
                "source_split": split,
                "source_label": label,
                "relative_image_path": relative(image_path, project_root),
                "sha256": digest(image_path),
                "width": width,
                "height": height,
                "exact_duplicate_group_id": "",
                "candidate_status": status,
                "candidate_reason": reason,
            }
            hashes[row["sha256"]].append(len(rows))
            rows.append(row)

    duplicate_groups = 0
    for indexes in (group for group in hashes.values() if len(group) > 1):
        duplicate_groups += 1
        group_id = f"exact_duplicate_{duplicate_groups:03d}"
        for index in indexes:
            rows[index]["exact_duplicate_group_id"] = group_id
            if rows[index]["candidate_status"] == "source_train_manhole_candidate":
                rows[index]["candidate_status"] = "hold_exact_duplicate_before_split"
                rows[index]["candidate_reason"] = "exact duplicate requires a cross-source split decision"

    counts = Counter((row["source_split"], row["source_label"]) for row in rows)
    report = {
        "source_id": SOURCE_ID,
        "source_url": SOURCE_URL,
        "source_license": SOURCE_LICENSE,
        "images_readable": len(rows),
        "counts_by_source_split_and_label": {
            f"{split}/{label}": counts[(split, label)] for split, label in sorted(counts)
        },
        "source_train_manhole_candidates": sum(
            row["candidate_status"] == "source_train_manhole_candidate" for row in rows
        ),
        "held_train_manhole_duplicates": sum(
            row["candidate_status"] == "hold_exact_duplicate_before_split" for row in rows
        ),
        "exact_duplicate_groups": duplicate_groups,
        "reserved_not_v2_candidates": sum(
            row["candidate_status"] == "reserved_not_v2_candidate" for row in rows
        ),
        "raw_data_changed": False,
        "training_status": "not_ready_no_final_v2_split_or_visual_sanity_review",
    }
    return rows, report


def write_outputs(rows: list[dict[str, Any]], report: dict[str, Any], manifest: Path, json_output: Path, markdown: Path) -> None:
    for path in (manifest, json_output, markdown):
        path.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    json_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    markdown.write_text(
        "# V2 Hugging Face Manhole-Cover Source Audit\n\n"
        f"- **Source:** [{SOURCE_ID}]({SOURCE_URL})\n"
        f"- **Licence record:** {SOURCE_LICENSE}\n"
        f"- **Audit date:** {date.today().isoformat()}\n"
        "- **Raw data changed:** No\n\n"
        "## Verified results\n\n"
        f"- Readable images: {report['images_readable']}\n"
        f"- Source-train manhole candidates: {report['source_train_manhole_candidates']}\n"
        f"- Held train-manhole exact duplicates: {report['held_train_manhole_duplicates']}\n"
        f"- Reserved non-candidates: {report['reserved_not_v2_candidates']}\n"
        f"- Exact duplicate groups across supplied splits: {report['exact_duplicate_groups']}\n\n"
        "## Boundary\n\n"
        "This is image-level manhole/void data. It supplies no bounding boxes, so it may support "
        "multi-class or multi-label lookalike learning only—not object detection. Only its official "
        "train/manhole images can enter the pre-split candidate inventory. Its void images and original "
        "validation/test images remain reserved. A final V2 split and visual sanity review are still required "
        "before training.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    rows, report = audit_dataset(args.data_dir, args.project_root)
    write_outputs(rows, report, args.manifest_output, args.json_output, args.markdown_output)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
