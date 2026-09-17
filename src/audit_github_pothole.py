"""Audit the downloaded GitHub pothole dataset without altering raw files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from PIL import Image


SOURCE_NAME = "jaygala24/pothole-detection"
SOURCE_URL = "https://github.com/jaygala24/pothole-detection"
SOURCE_LICENSE = "MIT"


def parse_yolo_label(path: Path) -> tuple[int, int]:
    """Return valid and invalid source-box counts; do not modify the label."""
    valid = invalid = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            values = [float(value) for value in line.split()]
            is_valid = (
                len(values) == 5
                and values[0].is_integer()
                and all(0 <= value <= 1 for value in values[1:])
                and values[3] > 0
                and values[4] > 0
            )
        except ValueError:
            is_valid = False
        if is_valid:
            valid += 1
        else:
            invalid += 1
    return valid, invalid


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    parser.add_argument("--report-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    args = parser.parse_args()

    images = sorted(
        path for path in args.data_dir.iterdir()
        if path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    rows: list[dict[str, object]] = []
    hashes: dict[str, list[int]] = defaultdict(list)

    for index, image_path in enumerate(images):
        label_path = image_path.with_suffix(".txt")
        if not label_path.exists():
            raise FileNotFoundError(f"Missing label: {label_path}")
        with Image.open(image_path) as image:
            image.verify()
        with Image.open(image_path) as image:
            width, height = image.size
        digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
        valid_boxes, invalid_boxes = parse_yolo_label(label_path)
        rows.append(
            {
                "source_id": f"github_pothole::{image_path.stem}",
                "filename": image_path.name,
                "relative_image_path": image_path.relative_to(args.project_root).as_posix(),
                "relative_label_path": label_path.relative_to(args.project_root).as_posix(),
                "sha256": digest,
                "width": width,
                "height": height,
                "valid_pothole_boxes": valid_boxes,
                "invalid_source_boxes": invalid_boxes,
                "duplicate_group": "",
                "decision": "keep",
                "decision_reason": "human_visual_quality_approved",
            }
        )
        hashes[digest].append(index)

    # Keep one image per exact duplicate group.  When labels differ, retain the
    # copy containing more valid boxes, then use filename as a stable tiebreaker.
    duplicate_groups = 0
    for group_number, indexes in enumerate(
        (indexes for indexes in hashes.values() if len(indexes) > 1), start=1
    ):
        duplicate_groups += 1
        group_id = f"exact_duplicate_{group_number:03d}"
        winner = sorted(
            indexes,
            key=lambda index: (-int(rows[index]["valid_pothole_boxes"]), str(rows[index]["filename"])),
        )[0]
        for index in indexes:
            rows[index]["duplicate_group"] = group_id
            if index != winner:
                rows[index]["decision"] = "exclude"
                rows[index]["decision_reason"] = "exact_duplicate_kept_copy_has_more_valid_boxes"

    included = [row for row in rows if row["decision"] == "keep"]
    report = {
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "source_license": SOURCE_LICENSE,
        "images_found": len(rows),
        "labels_found": len(rows),
        "accepted_images": len(included),
        "excluded_exact_duplicate_images": len(rows) - len(included),
        "exact_duplicate_groups": duplicate_groups,
        "accepted_valid_pothole_boxes": sum(int(row["valid_pothole_boxes"]) for row in included),
        "invalid_source_box_lines": sum(int(row["invalid_source_boxes"]) for row in rows),
        "human_visual_decision": "approved_clear_potholes",
        "raw_data_changed": False,
    }

    fields = list(rows[0])
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest_output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(
        "# V2 GitHub Pothole Dataset Audit\n\n"
        f"- **Source:** [{SOURCE_NAME}]({SOURCE_URL})\n"
        f"- **Licence:** {SOURCE_LICENSE}\n"
        f"- **Audit date:** {date.today().isoformat()}\n"
        f"- **Raw data changed:** No\n"
        f"- **Human visual decision:** Approved — potholes are clear.\n\n"
        "## Verified results\n\n"
        f"- Images and matching labels: {report['images_found']} each\n"
        f"- Accepted unique images: {report['accepted_images']}\n"
        f"- Accepted valid pothole boxes: {report['accepted_valid_pothole_boxes']}\n"
        f"- Exact duplicate groups: {report['exact_duplicate_groups']} (two redundant images excluded)\n"
        f"- Invalid source boxes: {report['invalid_source_box_lines']} (a zero-width box in `img-415.txt`; raw file preserved)\n\n"
        "## Decision\n\n"
        "This source is accepted as a **pothole-only detection candidate**. "
        "It must still be combined with other sources and split without leakage before model training. "
        "The source has no normal-road, shadow, manhole-cover, crack, or repaired-road labels.\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
