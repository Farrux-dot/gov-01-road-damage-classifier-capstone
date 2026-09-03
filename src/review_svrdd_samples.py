"""Create deterministic SVRDD visual-review contact sheets from training data.

This tool helps a reviewer inspect source labels before V2 label conversion. It
only reads raw source data and writes review images and a JSON record to an
ignored output folder. It does not create a model split or train a model.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


CATEGORY_NAMES = {
    0: "longitudinal_crack",
    1: "transverse_crack",
    2: "alligator_crack",
    3: "pothole",
    4: "manhole_cover",
    5: "longitudinal_patch",
    6: "transverse_patch",
}
PREVIEW_SIZE = (320, 320)
MARGIN = 14
LABEL_HEIGHT = 32
MAX_DISPLAY_NAME_LENGTH = 36


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read the supplied JSONL metadata without changing it."""
    with path.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def records_by_category(records: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    """Return each record once for every valid category it contains."""
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        objects = record.get("objects", {})
        categories = objects.get("categories", []) if isinstance(objects, dict) else []
        for category in sorted(set(categories)):
            if category in CATEGORY_NAMES:
                grouped[category].append(record)
    return dict(grouped)


def choose_samples(records: list[dict[str, Any]], count: int, seed: int, category: int) -> list[dict[str, Any]]:
    """Choose a repeatable, non-repeating sample for one category."""
    if count <= 0:
        raise ValueError("sample count must be positive")
    shuffled = list(records)
    random.Random(f"{seed}:{category}").shuffle(shuffled)
    return shuffled[:count]


def display_name(file_name: str) -> str:
    """Keep contact-sheet labels readable while the manifest keeps full paths."""
    name = Path(file_name).name
    if len(name) <= MAX_DISPLAY_NAME_LENGTH:
        return name
    return f"{name[:MAX_DISPLAY_NAME_LENGTH - 3]}..."


def annotated_preview(image_path: Path, record: dict[str, Any], focus_category: int) -> Image.Image:
    """Draw the focus class in red and all other supplied boxes in yellow."""
    with Image.open(image_path) as source:
        image = source.convert("RGB")
    draw = ImageDraw.Draw(image)
    objects = record["objects"]
    for bbox, category in zip(objects["bbox"], objects["categories"]):
        x, y, width, height = bbox
        color = "#e63946" if category == focus_category else "#f4d35e"
        draw.rectangle((x, y, x + width, y + height), outline=color, width=5)
    image.thumbnail(PREVIEW_SIZE)
    return image


def contact_sheet(previews: list[tuple[str, Image.Image]], title: str) -> Image.Image:
    """Make a simple two-column sheet suitable for manual review."""
    columns = 2
    rows = max(1, (len(previews) + columns - 1) // columns)
    cell_width = PREVIEW_SIZE[0] + 2 * MARGIN
    cell_height = PREVIEW_SIZE[1] + LABEL_HEIGHT + 2 * MARGIN
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height + LABEL_HEIGHT), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((MARGIN, MARGIN), title, fill="black", font=font)
    for index, (file_name, preview) in enumerate(previews):
        column = index % columns
        row = index // columns
        left = column * cell_width + MARGIN
        top = LABEL_HEIGHT + row * cell_height + MARGIN
        sheet.paste(preview, (left, top))
        draw.text((left, top + PREVIEW_SIZE[1] + 4), display_name(file_name), fill="black", font=font)
    return sheet


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images-dir", type=Path, required=True, help="SVRDD extracted training-image folder.")
    parser.add_argument("--metadata", type=Path, required=True, help="SVRDD train.metadata.jsonl file.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Ignored folder for contact sheets and review manifest.")
    parser.add_argument("--samples-per-class", type=int, default=8, help="Number of training images to show for each class.")
    parser.add_argument("--seed", type=int, default=42, help="Fixed selection seed for reproducible review.")
    args = parser.parse_args()

    records = read_jsonl(args.metadata)
    grouped = records_by_category(records)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "dataset": "SVRDD_YOLO",
        "review_split": "train",
        "seed": args.seed,
        "samples_per_class_requested": args.samples_per_class,
        "classes": {},
    }

    for category, category_name in CATEGORY_NAMES.items():
        candidates = grouped.get(category, [])
        selected = choose_samples(candidates, args.samples_per_class, args.seed, category)
        previews: list[tuple[str, Image.Image]] = []
        selected_names: list[str] = []
        for record in selected:
            file_name = record["file_name"]
            image_path = args.images_dir / file_name
            if not image_path.is_file():
                raise FileNotFoundError(f"Missing image named in metadata: {file_name}")
            previews.append((file_name, annotated_preview(image_path, record, category)))
            selected_names.append(file_name)
        output_name = f"{category:02d}_{category_name}_review.png"
        contact_sheet(previews, f"SVRDD train review: {category_name}").save(args.output_dir / output_name)
        manifest["classes"][category_name] = {
            "candidate_image_count": len(candidates),
            "selected_image_count": len(selected_names),
            "contact_sheet": output_name,
            "selected_files": selected_names,
        }

    manifest_path = args.output_dir / "review_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Created {len(CATEGORY_NAMES)} contact sheets in {args.output_dir}")
    print(f"Saved review manifest: {manifest_path}")


if __name__ == "__main__":
    main()
