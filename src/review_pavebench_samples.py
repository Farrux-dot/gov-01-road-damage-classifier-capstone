"""Create repeatable PaveBench contact sheets for human V2 label review.

This tool only reads the PaveBench classification folders. It does not change
labels, create a V2 split, combine sources, or train a model.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REVIEW_CLASSES = ("pothole", "patch", "negative")
CLASSIFICATION_SPLITS = ("train", "val", "test")
REVIEW_NOTES = {
    "pothole": "Candidate for Pothole; human review still required before use.",
    "patch": "Candidate for Repaired_road; do not map automatically.",
    "negative": "Generic negative only; do not relabel as a specific road look-alike.",
}
PREVIEW_SIZE = (512, 512)
MARGIN = 12
LABEL_HEIGHT = 28
COLUMNS = 2
MAX_DISPLAY_NAME_LENGTH = 32


def choose_samples(paths: list[Path], count: int, seed: int, category: str) -> list[Path]:
    """Choose a repeatable, non-repeating sample from one source class."""
    if count <= 0:
        raise ValueError("sample count must be positive")
    if not paths:
        raise ValueError(f"No images found for review class: {category}")
    shuffled = sorted(paths, key=lambda path: path.name)
    random.Random(f"{seed}:{category}").shuffle(shuffled)
    return shuffled[:count]


def category_image_paths(classification_dir: Path, category: str) -> list[Path]:
    """Return JPEGs from all supplied classification splits for one class."""
    paths: list[Path] = []
    for split in CLASSIFICATION_SPLITS:
        paths.extend((classification_dir / split / category).glob("*.jpg"))
    return paths


def display_name(path: Path) -> str:
    """Keep contact-sheet filenames readable."""
    if len(path.name) <= MAX_DISPLAY_NAME_LENGTH:
        return path.name
    return f"{path.stem[:MAX_DISPLAY_NAME_LENGTH - 7]}...{path.suffix}"


def preview(path: Path) -> Image.Image:
    """Load one image without enlarging it beyond its original detail."""
    with Image.open(path) as source:
        image = source.convert("RGB")
    image.thumbnail(PREVIEW_SIZE)
    return image


def contact_sheet(selected: list[Path], title: str) -> Image.Image:
    """Build a two-column sheet that preserves 512px source detail."""
    rows = max(1, (len(selected) + COLUMNS - 1) // COLUMNS)
    cell_width = PREVIEW_SIZE[0] + 2 * MARGIN
    cell_height = PREVIEW_SIZE[1] + LABEL_HEIGHT + 2 * MARGIN
    sheet = Image.new("RGB", (COLUMNS * cell_width, rows * cell_height + LABEL_HEIGHT), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((MARGIN, MARGIN), title, fill="black", font=font)
    for index, path in enumerate(selected):
        image = preview(path)
        column = index % COLUMNS
        row = index // COLUMNS
        left = column * cell_width + MARGIN
        top = LABEL_HEIGHT + row * cell_height + MARGIN
        sheet.paste(image, (left, top))
        draw.text((left, top + PREVIEW_SIZE[1] + 4), display_name(path), fill="black", font=font)
    return sheet


def review_rows(selected: list[Path], category: str, classification_dir: Path) -> list[dict[str, str]]:
    """Create blank, traceable human-review rows for the displayed images."""
    return [
        {
            "source_category": category,
            "source_file": path.name,
            "source_path": path.relative_to(classification_dir).as_posix(),
            "human_decision": "pending",
            "reviewer_note": "",
        }
        for path in selected
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--classification-dir",
        type=Path,
        required=True,
        help="PaveBench Distress_Classification folder containing class subfolders.",
    )
    parser.add_argument("--output-dir", type=Path, required=True, help="Ignored folder for contact sheets and manifest.")
    parser.add_argument("--samples-per-class", type=int, default=12, help="Number of images to show for each review class.")
    parser.add_argument("--seed", type=int, default=42, help="Fixed selection seed for reproducible review.")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "dataset": "PaveBench",
        "source_task": "Distress_Classification",
        "seed": args.seed,
        "samples_per_class_requested": args.samples_per_class,
        "review_status": "pending_human_review",
        "classes": {},
    }
    all_review_rows: list[dict[str, str]] = []

    for category in REVIEW_CLASSES:
        candidates = category_image_paths(args.classification_dir, category)
        selected = choose_samples(candidates, args.samples_per_class, args.seed, category)
        output_name = f"pavebench_{category}_review.png"
        contact_sheet(selected, f"PaveBench review: {category}").save(args.output_dir / output_name)
        manifest["classes"][category] = {
            "candidate_image_count": len(candidates),
            "selected_image_count": len(selected),
            "contact_sheet": output_name,
            "review_note": REVIEW_NOTES[category],
            "selected_files": [path.name for path in selected],
        }
        all_review_rows.extend(review_rows(selected, category, args.classification_dir))

    manifest_path = args.output_dir / "review_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    queue_path = args.output_dir / "human_review_queue.csv"
    with queue_path.open("w", newline="", encoding="utf-8") as queue_file:
        writer = csv.DictWriter(queue_file, fieldnames=all_review_rows[0].keys())
        writer.writeheader()
        writer.writerows(all_review_rows)
    print(f"Created {len(REVIEW_CLASSES)} PaveBench contact sheets in {args.output_dir}")
    print(f"Saved review manifest: {manifest_path}")
    print(f"Saved human review queue: {queue_path}")


if __name__ == "__main__":
    main()
