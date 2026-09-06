"""Create deterministic contact sheets for manually reviewing V1 Normal images.

The V1 `Normal` label only means "not labelled as pothole".  This tool does
not relabel, copy, split, or train on any image.  It creates an ignored local
review aid plus a manifest so a reviewer can record an honest decision later.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PREVIEW_SIZE = (192, 192)
COLUMNS = 4
MARGIN = 12
LABEL_HEIGHT = 22


def image_paths(normal_dir: Path) -> list[Path]:
    """Return supported images in a stable order."""
    return sorted(
        path for path in normal_dir.iterdir() if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )


def choose_samples(paths: list[Path], count: int, seed: int) -> list[Path]:
    """Choose non-repeating, deterministic images for a manual review."""
    if count <= 0:
        raise ValueError("sample count must be positive")
    shuffled = list(paths)
    random.Random(seed).shuffle(shuffled)
    return shuffled[:count]


def preview(path: Path) -> Image.Image:
    """Open an image and enlarge it with nearest-neighbour pixels for inspection."""
    with Image.open(path) as source:
        image = source.convert("RGB")
    return image.resize(PREVIEW_SIZE, Image.Resampling.NEAREST)


def contact_sheet(paths: list[Path], title: str) -> Image.Image:
    """Build a compact grid with source file names."""
    rows = max(1, (len(paths) + COLUMNS - 1) // COLUMNS)
    cell_width = PREVIEW_SIZE[0] + 2 * MARGIN
    cell_height = PREVIEW_SIZE[1] + LABEL_HEIGHT + 2 * MARGIN
    sheet = Image.new("RGB", (COLUMNS * cell_width, rows * cell_height + LABEL_HEIGHT), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((MARGIN, 5), title, fill="black", font=font)
    for index, path in enumerate(paths):
        column = index % COLUMNS
        row = index // COLUMNS
        left = column * cell_width + MARGIN
        top = LABEL_HEIGHT + row * cell_height + MARGIN
        sheet.paste(preview(path), (left, top))
        draw.text((left, top + PREVIEW_SIZE[1] + 4), path.name, fill="black", font=font)
    return sheet


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--normal-dir", type=Path, required=True, help="V1 clean train/Normal folder.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Ignored folder for contact sheets and manifest.")
    parser.add_argument("--sample-count", type=int, default=24, help="Number of Normal images to inspect.")
    parser.add_argument("--sheet-size", type=int, default=8, help="Images per contact sheet.")
    parser.add_argument("--seed", type=int, default=42, help="Fixed selection seed for reproducible review.")
    args = parser.parse_args()

    if not args.normal_dir.is_dir():
        raise FileNotFoundError(f"V1 Normal folder not found: {args.normal_dir}")
    if args.sheet_size <= 0:
        raise ValueError("sheet size must be positive")
    candidates = image_paths(args.normal_dir)
    selected = choose_samples(candidates, args.sample_count, args.seed)
    if not selected:
        raise ValueError("No supported images found in the V1 Normal folder")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    sheet_names: list[str] = []
    for start in range(0, len(selected), args.sheet_size):
        batch = selected[start : start + args.sheet_size]
        number = start // args.sheet_size + 1
        sheet_name = f"v1_normal_review_{number:02d}.png"
        contact_sheet(batch, f"V1 Normal training review {number}").save(args.output_dir / sheet_name)
        sheet_names.append(sheet_name)

    manifest = {
        "dataset": "V1_clean_split",
        "source_split": "train",
        "source_label": "Normal",
        "review_purpose": "Decide whether selected images may later be considered clear normal asphalt; do not change labels automatically.",
        "seed": args.seed,
        "candidate_image_count": len(candidates),
        "selected_image_count": len(selected),
        "contact_sheets": sheet_names,
        "selected_files": [path.name for path in selected],
        "allowed_reviewer_decisions": [
            "clear_normal_asphalt",
            "shadow_or_lighting",
            "puddle_or_reflection",
            "road_stain_or_marking",
            "repair_or_patch",
            "unpaved_or_other",
            "uncertain",
        ],
    }
    manifest_path = args.output_dir / "review_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Created {len(sheet_names)} V1 Normal review sheet(s) in {args.output_dir}")
    print(f"Saved review manifest: {manifest_path}")


if __name__ == "__main__":
    main()
