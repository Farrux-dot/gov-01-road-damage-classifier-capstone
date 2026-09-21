"""Create paired contact sheets and a pending review manifest for V2 pairs."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from PIL import Image, ImageDraw


def preview(path: Path, label: str) -> Image.Image:
    with Image.open(path) as image:
        copy = image.convert("RGB")
    scale = min(360 / copy.width, 260 / copy.height)
    copy = copy.resize((max(1, round(copy.width * scale)), max(1, round(copy.height * scale))))
    card = Image.new("RGB", (380, 310), "white")
    card.paste(copy, ((380 - copy.width) // 2, 5))
    ImageDraw.Draw(card).text((8, 270), label[:58], fill="black")
    return card


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pairs-per-sheet", type=int, default=4)
    args = parser.parse_args()
    root = args.queue.resolve().parents[1]
    with args.queue.open(newline="", encoding="utf-8-sig") as handle:
        pairs = list(csv.DictReader(handle))
    resolved_path = root / "docs" / "v2_multiclass_split_manifest_near_duplicate_resolved.csv"
    with resolved_path.open(newline="", encoding="utf-8-sig") as handle:
        locations = {row["candidate_id"]: row["source_image_path"] for row in csv.DictReader(handle)}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, pair in enumerate(pairs, start=1):
        left = root / locations[pair["candidate_id_a"]]
        right = root / locations[pair["candidate_id_b"]]
        if not left.is_file() or not right.is_file():
            raise FileNotFoundError(f"Missing review image for pair {index}")
        sheet_number = (index - 1) // args.pairs_per_sheet + 1
        rows.append({**pair, "pair_id": f"near-{index:03d}", "left_image_path": left.relative_to(root).as_posix(), "right_image_path": right.relative_to(root).as_posix(), "contact_sheet": f"near_duplicate_pairs_{sheet_number:02d}.png", "decision": "pending_human_review", "reviewer_note": ""})
    fields = list(rows[0])
    with args.manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    for sheet_number in range(1, (len(rows) - 1) // args.pairs_per_sheet + 2):
        selected = rows[(sheet_number - 1) * args.pairs_per_sheet:sheet_number * args.pairs_per_sheet]
        canvas = Image.new("RGB", (780, 80 + len(selected) * 320), "#eeeeee")
        draw = ImageDraw.Draw(canvas); draw.text((10, 10), f"V2 near-duplicate review — sheet {sheet_number}", fill="black")
        for offset, row in enumerate(selected):
            y = 50 + offset * 320
            canvas.paste(preview(root / row["left_image_path"], f"{row['pair_id']} A | {row['split_a']} | {row['label_a']}"), (10, y))
            canvas.paste(preview(root / row["right_image_path"], f"{row['pair_id']} B | {row['split_b']} | {row['label_b']}"), (390, y))
        canvas.save(args.output_dir / f"near_duplicate_pairs_{sheet_number:02d}.png")
    print(f"Pending pairs: {len(rows)}")
    print(f"Manifest: {args.manifest}")
    print(f"Contact sheets: {args.output_dir}")


if __name__ == "__main__":
    main()
