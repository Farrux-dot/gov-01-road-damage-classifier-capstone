"""Prepare a review-only shortlist of possible road-shadow images.

This is a conservative data-audit helper, not a machine-learning model. It
scans eligible StreetSurfaceVis training images that were not already reviewed,
then ranks visual dark regions that might be shadows. Every selected image
still needs a human decision before it can enter the V2 inventory.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


REVIEW_FILES = (
    "v2_shadow_multilabel_manifest.csv",
    "v2_no_shadow_manifest.csv",
    "v2_streetsurfacevis_shadow_review_decisions.csv",
    "v2_streetsurfacevis_shadow_review_round2_decisions.csv",
    "v2_streetsurfacevis_no_shadow_review_decisions.csv",
)
OUTPUT_FIELDS = (
    "review_id", "candidate_id", "source_dataset", "source_split",
    "source_record_id", "source_image_path", "primary_road_label",
    "heuristic_score", "selection_reason", "human_decision", "reviewer_notes",
)


@dataclass(frozen=True)
class ScoredImage:
    row: dict[str, str]
    score: float
    image_hash: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def candidate_id_from_row(row: dict[str, str]) -> str | None:
    """Read a StreetSurfaceVis record ID from the known review CSV shapes."""
    for field in ("source_record_id", "image_id", "candidate_id"):
        value = (row.get(field) or "").strip()
        if not value:
            continue
        if "::" in value:
            value = value.rsplit("::", 1)[-1]
        if value.isdigit():
            return value
    return None


def reviewed_candidate_ids(docs_dir: Path) -> set[str]:
    """Return every StreetSurfaceVis record previously shown to the reviewer."""
    reviewed: set[str] = set()
    for name in REVIEW_FILES:
        path = docs_dir / name
        if not path.is_file():
            continue
        for row in read_csv(path):
            source = row.get("source_dataset") or row.get("source_id") or "StreetSurfaceVis"
            if source != "StreetSurfaceVis":
                continue
            identifier = candidate_id_from_row(row)
            if identifier is not None:
                reviewed.add(identifier)
    return reviewed


def shadow_like_score(image: Image.Image) -> float:
    """Score local dark regions; a high score is only a review priority."""
    grayscale = image.convert("L")
    grayscale.thumbnail((320, 320))
    pixels = np.asarray(grayscale, dtype=np.float32)
    if pixels.size == 0:
        return 0.0
    blurred = np.asarray(grayscale.filter(ImageFilter.GaussianBlur(radius=10)), dtype=np.float32)
    local_darkening = np.maximum(blurred - pixels, 0.0) / 255.0
    plausible_road_tone = (pixels < 210.0) & (blurred > 70.0)
    shadow_like = plausible_road_tone & (local_darkening >= 0.055)
    return float(shadow_like.mean()) * 0.70 + float(np.percentile(local_darkening, 90)) * 0.30


def average_hash(image: Image.Image) -> str:
    grayscale = image.convert("L").resize((8, 8))
    values = np.asarray(grayscale, dtype=np.float32)
    return "".join("1" if value >= values.mean() else "0" for value in values.ravel())


def hamming_distance(left: str, right: str) -> int:
    return sum(one != two for one, two in zip(left, right))


def select_diverse(scored: list[ScoredImage], maximum: int) -> list[ScoredImage]:
    """Keep high-scoring candidates while avoiding visually near-identical copies."""
    per_label: dict[str, list[ScoredImage]] = defaultdict(list)
    for item in sorted(scored, key=lambda item: item.score, reverse=True):
        per_label[item.row["candidate_label"]].append(item)
    selected: list[ScoredImage] = []
    selected_hashes: list[str] = []
    labels = sorted(per_label)
    while len(selected) < maximum:
        progress = False
        for label in labels:
            if not per_label[label] or len(selected) >= maximum:
                continue
            item = per_label[label].pop(0)
            if any(hamming_distance(item.image_hash, existing) <= 3 for existing in selected_hashes):
                continue
            selected.append(item)
            selected_hashes.append(item.image_hash)
            progress = True
        if not progress:
            break
    return selected


def prepare(repo_root: Path, output_csv: Path, output_dir: Path, maximum: int = 120) -> dict[str, int]:
    docs_dir = repo_root / "docs"
    candidates = read_csv(docs_dir / "v2_streetsurfacevis_candidate_manifest.csv")
    reviewed = reviewed_candidate_ids(docs_dir)
    eligible = [row for row in candidates if row.get("official_train") == "True" and row.get("resolution_decision") == "eligible" and row.get("image_id") not in reviewed]
    if not eligible:
        raise ValueError("No unreviewed eligible StreetSurfaceVis images remain")
    scored: list[ScoredImage] = []
    unreadable = 0
    for row in eligible:
        try:
            with Image.open(repo_root / row["relative_image_path"]) as image:
                scored.append(ScoredImage(row, shadow_like_score(image), average_hash(image)))
        except (OSError, ValueError):
            unreadable += 1
    selected = select_diverse(scored, maximum)
    if not selected:
        raise ValueError("No readable unreviewed StreetSurfaceVis images remain")
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, str]] = []
    for index, item in enumerate(selected, start=1):
        row = item.row
        source = repo_root / row["relative_image_path"]
        shutil.copy2(source, output_dir / f"{index:03d}_{row['candidate_label']}_{row['image_id']}{source.suffix.lower()}")
        records.append({
            "review_id": f"SHC-{index:03d}",
            "candidate_id": f"streetsurfacevis::train::{row['image_id']}",
            "source_dataset": "StreetSurfaceVis", "source_split": "train",
            "source_record_id": row["image_id"], "source_image_path": row["relative_image_path"],
            "primary_road_label": row["candidate_label"], "heuristic_score": f"{item.score:.6f}",
            "selection_reason": "unreviewed eligible road image with a visually dark local region; human review required",
            "human_decision": "pending", "reviewer_notes": "",
        })
    write_csv(output_csv, records)
    return {
        "eligible_before_review_exclusion": sum(row.get("official_train") == "True" and row.get("resolution_decision") == "eligible" for row in candidates),
        "previously_reviewed_excluded": len(reviewed),
        "unreviewed_images_scanned": len(eligible),
        "unreadable_images_skipped": unreadable,
        "review_candidates_created": len(records),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-csv", type=Path, default=Path("docs/v2_streetsurfacevis_shadow_heuristic_candidates.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/v2/streetsurfacevis_shadow_heuristic_candidates"))
    parser.add_argument("--max-candidates", type=int, default=120)
    args = parser.parse_args()
    if args.max_candidates <= 0:
        raise ValueError("--max-candidates must be positive")
    root = args.repo_root.resolve()
    output_csv = args.output_csv if args.output_csv.is_absolute() else root / args.output_csv
    output_dir = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    print(json.dumps(prepare(root, output_csv, output_dir, args.max_candidates), indent=2))


if __name__ == "__main__":
    main()
