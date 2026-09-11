from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, UnidentifiedImageError


CLASS_NAMES = {
    0: "HMV",
    1: "LMV",
    2: "Pedestrian",
    3: "RoadDamages",
    4: "SpeedBump",
    5: "UnsurfacedRoad",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def parse_yolo_row(line: str) -> int | None:
    """Return the source class ID when one normalized YOLO row is valid."""
    parts = line.split()
    try:
        if len(parts) != 5:
            return None
        class_id = int(parts[0])
        coords = [float(value) for value in parts[1:]]
    except ValueError:
        return None
    if class_id not in CLASS_NAMES:
        return None
    if not all(0 <= value <= 1 for value in coords):
        return None
    if coords[2] <= 0 or coords[3] <= 0:
        return None
    return class_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report: dict[str, object] = {
        "dataset": "RAD Road Anomaly Detection v3",
        "source_class_names": {str(key): value for key, value in CLASS_NAMES.items()},
        "splits": {},
    }
    hashes: dict[str, list[str]] = defaultdict(list)
    all_boxes: Counter[str] = Counter()
    all_images_with_class: Counter[str] = Counter()
    hard_errors: list[str] = []

    for split in ("train", "valid", "test"):
        image_dir = args.root / split / "images"
        label_dir = args.root / split / "labels"
        images = {path.stem: path for path in image_dir.glob("*.jpg")}
        labels = {path.stem: path for path in label_dir.glob("*.txt")}
        missing_labels = sorted(set(images) - set(labels))
        missing_images = sorted(set(labels) - set(images))
        unreadable: list[str] = []
        invalid_rows: list[str] = []
        dimensions: Counter[str] = Counter()
        boxes: Counter[str] = Counter()
        images_with_class: Counter[str] = Counter()
        empty_labels = 0

        for stem, image_path in images.items():
            try:
                with Image.open(image_path) as image:
                    image.verify()
                with Image.open(image_path) as image:
                    dimensions[f"{image.width}x{image.height}"] += 1
            except (OSError, UnidentifiedImageError):
                unreadable.append(image_path.name)
                continue

            hashes[digest(image_path)].append(f"{split}/{image_path.name}")
            label_path = labels.get(stem)
            if label_path is None:
                continue
            text = label_path.read_text(encoding="utf-8").strip()
            if not text:
                empty_labels += 1
                continue
            present: set[int] = set()
            for line_number, line in enumerate(text.splitlines(), start=1):
                item = f"{label_path.name}:{line_number}"
                class_id = parse_yolo_row(line)
                if class_id is None:
                    invalid_rows.append(item)
                    continue
                boxes[CLASS_NAMES[class_id]] += 1
                present.add(class_id)
            for class_id in present:
                images_with_class[CLASS_NAMES[class_id]] += 1

        all_boxes.update(boxes)
        all_images_with_class.update(images_with_class)
        split_report = {
            "image_count": len(images),
            "label_file_count": len(labels),
            "missing_label_count": len(missing_labels),
            "missing_image_count": len(missing_images),
            "unreadable_image_count": len(unreadable),
            "empty_label_file_count": empty_labels,
            "invalid_label_row_count": len(invalid_rows),
            "boxes_by_source_class": dict(sorted(boxes.items())),
            "images_with_source_class": dict(sorted(images_with_class.items())),
            "resolution_counts": dict(sorted(dimensions.items())),
            "examples": {
                "missing_labels": missing_labels[:10],
                "missing_images": missing_images[:10],
                "unreadable_images": unreadable[:10],
                "invalid_label_rows": invalid_rows[:10],
            },
        }
        report["splits"][split] = split_report
        for key in ("missing_label_count", "missing_image_count", "unreadable_image_count", "invalid_label_row_count"):
            if split_report[key]:
                hard_errors.append(f"{split}: {key}={split_report[key]}")

    duplicate_groups = [items for items in hashes.values() if len(items) > 1]
    cross_split_groups = [
        items
        for items in duplicate_groups
        if len({item.split("/", 1)[0] for item in items}) > 1
    ]
    report["boxes_by_source_class_total"] = dict(sorted(all_boxes.items()))
    report["images_with_source_class_total"] = dict(sorted(all_images_with_class.items()))
    report["exact_duplicate_group_count"] = len(duplicate_groups)
    report["exact_duplicate_group_count_across_source_splits"] = len(cross_split_groups)
    report["exact_duplicate_examples_across_source_splits"] = cross_split_groups[:25]
    report["hard_errors"] = hard_errors
    report["warnings"] = []
    if cross_split_groups:
        report["warnings"].append("Exact duplicate images cross the source-provided splits; rebuild splits before modeling.")
    report["audit_status"] = "needs_review" if hard_errors or report["warnings"] else "passed"
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
