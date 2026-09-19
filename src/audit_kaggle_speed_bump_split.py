"""Audit the full Kaggle speed-bump train/test package without changing raw data.

Only exact-unique, non-sequence images from the supplied ``train/bump`` folder
can become V2 candidates. The supplied ``test/bump`` folder stays reserved and
is checked for exact-content overlap before any later integration.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from PIL import Image


SOURCE_URL = "https://www.kaggle.com/datasets/ziya07/speed-bump-dataset"
SOURCE_LICENSE = "CC0 / Public Domain stated on the Kaggle dataset page; recheck before redistribution"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
SEQUENCE_NAME = re.compile(r"^MVI_.+ \d+$", re.IGNORECASE)
FIELDNAMES = (
    "source_record_id", "source_split", "relative_image_path", "sha256", "width", "height",
    "sequence_risk", "exact_duplicate_group_id", "decision", "decision_reason",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repository_relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def audit_dataset(data_dir: Path, project_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    expected = {split: data_dir / split / "bump" for split in ("train", "test")}
    for split, folder in expected.items():
        if not folder.is_dir():
            raise FileNotFoundError(f"Missing source {split} bump folder: {folder}")

    rows: list[dict[str, Any]] = []
    by_hash: dict[str, list[int]] = defaultdict(list)
    for split, folder in expected.items():
        for image_path in sorted(path for path in folder.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES):
            with Image.open(image_path) as image:
                image.verify()
            with Image.open(image_path) as image:
                width, height = image.size
            sequence_risk = bool(SEQUENCE_NAME.match(image_path.stem))
            if split == "test":
                decision = "reserve_official_source_test"
                reason = "supplied source test folder stays out of V2 candidate training pool"
            elif sequence_risk:
                decision = "exclude_sequence_risk"
                reason = "MVI numbered filename indicates consecutive recording frames"
            else:
                decision = "keep_train_speed_bump_candidate"
                reason = "source train bump label with no MVI sequence-style filename"
            row = {
                "source_record_id": f"{split}::bump::{image_path.name}",
                "source_split": split,
                "relative_image_path": repository_relative(image_path, project_root),
                "sha256": sha256(image_path),
                "width": width,
                "height": height,
                "sequence_risk": str(sequence_risk).lower(),
                "exact_duplicate_group_id": "",
                "decision": decision,
                "decision_reason": reason,
            }
            by_hash[row["sha256"]].append(len(rows))
            rows.append(row)

    duplicate_groups = 0
    for indexes in (group for group in by_hash.values() if len(group) > 1):
        duplicate_groups += 1
        group_id = f"exact_duplicate_{duplicate_groups:04d}"
        has_test = any(rows[index]["source_split"] == "test" for index in indexes)
        train_keepers = [
            index for index in indexes
            if rows[index]["decision"] == "keep_train_speed_bump_candidate"
        ]
        winner = min(train_keepers, key=lambda index: str(rows[index]["source_record_id"])) if train_keepers else None
        for index in indexes:
            rows[index]["exact_duplicate_group_id"] = group_id
            if rows[index]["decision"] != "keep_train_speed_bump_candidate":
                continue
            if has_test:
                rows[index]["decision"] = "hold_cross_split_exact_duplicate"
                rows[index]["decision_reason"] = "exact duplicate also appears in supplied source test folder"
            elif index != winner:
                rows[index]["decision"] = "exclude_exact_duplicate_before_split"
                rows[index]["decision_reason"] = "exact duplicate; stable source-record winner retained"

    decisions = Counter(str(row["decision"]) for row in rows)
    report = {
        "source_url": SOURCE_URL,
        "source_license": SOURCE_LICENSE,
        "images_readable": len(rows),
        "readable_by_split": dict(sorted(Counter(str(row["source_split"]) for row in rows).items())),
        "kept_train_speed_bump_candidates": decisions["keep_train_speed_bump_candidate"],
        "reserved_official_source_test_images": decisions["reserve_official_source_test"],
        "excluded_sequence_risk_train_images": decisions["exclude_sequence_risk"],
        "excluded_exact_duplicate_train_images": decisions["exclude_exact_duplicate_before_split"],
        "held_cross_split_exact_duplicate_train_images": decisions["hold_cross_split_exact_duplicate"],
        "exact_duplicate_groups": duplicate_groups,
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
        "# V2 Kaggle Speed-Bump Train/Test Package Audit\n\n"
        f"- **Source:** [Speed Bump Dataset]({SOURCE_URL})\n"
        f"- **Licence record:** {SOURCE_LICENSE}\n"
        f"- **Audit date:** {date.today().isoformat()}\n"
        "- **Raw data changed:** No\n\n"
        "## Verified results\n\n"
        f"- Readable labelled bump images: {report['images_readable']}\n"
        f"- Kept non-sequence, exact-unique train candidates: {report['kept_train_speed_bump_candidates']}\n"
        f"- Reserved supplied source-test images: {report['reserved_official_source_test_images']}\n"
        f"- Excluded MVI sequence-risk train images: {report['excluded_sequence_risk_train_images']}\n"
        f"- Excluded redundant exact-duplicate train images: {report['excluded_exact_duplicate_train_images']}\n"
        f"- Held train images duplicated in source test: {report['held_cross_split_exact_duplicate_train_images']}\n"
        f"- Exact duplicate groups across train and test: {report['exact_duplicate_groups']}\n\n"
        "## Decision boundary\n\n"
        "Only retained train records can be considered for future V2 training. The supplied source-test folder is reserved and is never used for training or tuning. This audit only checks exact duplicates; it does not certify that visually similar video frames are independent.\n",
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
