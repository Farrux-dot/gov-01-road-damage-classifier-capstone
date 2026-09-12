from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, UnidentifiedImageError


REVIEWED_CLASSES = ("asphalt", "compacted", "gravel", "ground")
SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def is_below_minimum_resolution(width: int, height: int, minimum_side: int = 224) -> bool:
    """Return True when either image side is smaller than the review minimum."""
    if width <= 0 or height <= 0 or minimum_side <= 0:
        raise ValueError("Image dimensions and minimum_side must be positive.")
    return width < minimum_side or height < minimum_side


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def audit(root: Path, minimum_side: int = 224) -> dict[str, object]:
    hashes: dict[str, list[str]] = defaultdict(list)
    class_counts: dict[str, int] = {}
    below_minimum: dict[str, int] = {}
    unreadable: list[str] = []
    dimensions: Counter[str] = Counter()
    modes: Counter[str] = Counter()
    suffixes: Counter[str] = Counter()

    for class_name in REVIEWED_CLASSES:
        class_dir = root / class_name
        if not class_dir.is_dir():
            raise FileNotFoundError(f"Missing expected class directory: {class_dir}")
        images = sorted(
            path for path in class_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
        )
        class_counts[class_name] = len(images)
        low_resolution_count = 0
        for image_path in images:
            suffixes[image_path.suffix.lower()] += 1
            hashes[digest(image_path)].append(f"{class_name}/{image_path.name}")
            try:
                with Image.open(image_path) as image:
                    image.verify()
                with Image.open(image_path) as image:
                    dimensions[f"{image.width}x{image.height}"] += 1
                    modes[image.mode] += 1
                    if is_below_minimum_resolution(
                        image.width, image.height, minimum_side
                    ):
                        low_resolution_count += 1
            except (OSError, UnidentifiedImageError):
                unreadable.append(f"{class_name}/{image_path.name}")
        below_minimum[class_name] = low_resolution_count

    duplicate_groups = [items for items in hashes.values() if len(items) > 1]
    cross_class_groups = [
        items
        for items in duplicate_groups
        if len({item.split("/", 1)[0] for item in items}) > 1
    ]
    total = sum(class_counts.values())
    low_resolution_total = sum(below_minimum.values())
    return {
        "dataset": "Deep Pavements Dataset",
        "reviewed_classes": list(REVIEWED_CLASSES),
        "minimum_side": minimum_side,
        "class_counts": class_counts,
        "total_image_count": total,
        "unreadable_image_count": len(unreadable),
        "unreadable_examples": unreadable[:20],
        "images_below_minimum_by_class": below_minimum,
        "images_below_minimum_total": low_resolution_total,
        "images_meeting_minimum_total": total - low_resolution_total,
        "below_minimum_fraction": low_resolution_total / total if total else None,
        "unique_resolution_count": len(dimensions),
        "resolution_counts": dict(sorted(dimensions.items())),
        "image_modes": dict(sorted(modes.items())),
        "file_suffixes": dict(sorted(suffixes.items())),
        "exact_duplicate_group_count": len(duplicate_groups),
        "cross_class_exact_duplicate_group_count": len(cross_class_groups),
        "cross_class_exact_duplicate_examples": cross_class_groups[:20],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--minimum-side", type=int, default=224)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = audit(args.root, args.minimum_side)
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
