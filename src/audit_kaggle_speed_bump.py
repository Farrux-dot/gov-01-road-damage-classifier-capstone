"""Audit the approved Kaggle speed-bump source without changing raw files.

Only non-sequence images from the source ``bump`` folder are candidates for the
supporting V2 speed-bump lookalike condition. The source has no official split
and no boxes, so it remains a pre-split image-level source.
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
LABELS = ("bump", "crack", "potholes", "road")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
SEQUENCE_NAME = re.compile(r"^MVI_.+ \d+$", re.IGNORECASE)
FIELDNAMES = (
    "source_record_id", "source_label", "relative_image_path", "sha256", "width", "height",
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
    found_labels = tuple(sorted(path.name for path in data_dir.iterdir() if path.is_dir()))
    if found_labels != LABELS:
        raise ValueError(f"Expected labels {LABELS}, found {found_labels}")
    rows: list[dict[str, Any]] = []
    by_hash: dict[str, list[int]] = defaultdict(list)
    for label in LABELS:
        for image_path in sorted(path for path in (data_dir / label).iterdir() if path.suffix.lower() in IMAGE_SUFFIXES):
            with Image.open(image_path) as image:
                image.verify()
            with Image.open(image_path) as image:
                width, height = image.size
            sequence_risk = bool(SEQUENCE_NAME.match(image_path.stem))
            decision = "exclude_not_speed_bump_source_label"
            reason = "not used for the speed-bump supporting-class task"
            if label == "bump" and sequence_risk:
                decision = "exclude_sequence_risk"
                reason = "MVI numbered filename indicates consecutive recording frames"
            elif label == "bump":
                decision = "keep_speed_bump_candidate"
                reason = "source bump label with no MVI sequence-style filename"
            row = {
                "source_record_id": f"{label}::{image_path.name}",
                "source_label": label,
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
        group_id = f"exact_duplicate_{duplicate_groups:03d}"
        candidate_indexes = [
            index for index in indexes if rows[index]["decision"] == "keep_speed_bump_candidate"
        ]
        winner = min(candidate_indexes, key=lambda index: str(rows[index]["source_record_id"])) if candidate_indexes else None
        for index in indexes:
            rows[index]["exact_duplicate_group_id"] = group_id
            if rows[index]["decision"] == "keep_speed_bump_candidate" and index != winner:
                rows[index]["decision"] = "exclude_exact_duplicate_before_split"
                rows[index]["decision_reason"] = "exact duplicate; stable source-record winner retained"

    decisions = Counter(str(row["decision"]) for row in rows)
    report = {
        "source_url": SOURCE_URL,
        "source_license": SOURCE_LICENSE,
        "images_readable": len(rows),
        "counts_by_source_label": dict(sorted(Counter(str(row["source_label"]) for row in rows).items())),
        "kept_speed_bump_candidates": decisions["keep_speed_bump_candidate"],
        "excluded_sequence_risk_bump_images": decisions["exclude_sequence_risk"],
        "excluded_exact_duplicate_candidate_images": decisions["exclude_exact_duplicate_before_split"],
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
        "# V2 Kaggle Speed-Bump Source Audit\n\n"
        f"- **Source:** [Speed Bump Dataset]({SOURCE_URL})\n"
        f"- **Licence record:** {SOURCE_LICENSE}\n"
        f"- **Audit date:** {date.today().isoformat()}\n"
        "- **Raw data changed:** No\n\n"
        "## Verified results\n\n"
        f"- Readable labelled images: {report['images_readable']}\n"
        f"- Kept non-sequence speed-bump candidates: {report['kept_speed_bump_candidates']}\n"
        f"- Excluded MVI sequence-risk bump images: {report['excluded_sequence_risk_bump_images']}\n"
        f"- Excluded redundant exact-duplicate bump images: {report['excluded_exact_duplicate_candidate_images']}\n"
        f"- Exact duplicate groups: {report['exact_duplicate_groups']}\n\n"
        "## Decision boundary\n\n"
        "This audit uses only source-labelled `bump` images without the numbered `MVI_...` recording-frame pattern. "
        "The source `crack`, `potholes`, and `road` folders are deliberately not added by this task. "
        "No bounding boxes or official source splits are available. The kept records are pre-split supporting candidates only; "
        "they require a final V2 split and visual sanity review before training.\n",
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
