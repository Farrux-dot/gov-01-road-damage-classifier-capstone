"""Build a deterministic human-review sample of SVRDD manhole crops.

This tool reads only the SVRDD source training annotations and images. It
creates preview images and a pending review manifest. It does not change raw
data, approve labels, create final splits, or train a model.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageDraw


REQUIRED_ANNOTATION_NAME = "train.v2.jsonl"
DECISION_OPTIONS = (
    "approve_manhole",
    "reject_not_manhole",
    "reject_unclear",
    "reject_mixed_condition",
    "wrong_box",
)
FIELDNAMES = (
    "sample_id",
    "candidate_id",
    "source_image_id",
    "region",
    "source_image_path",
    "preview_file",
    "target_box_xywh",
    "crop_box_xyxy",
    "target_min_side_px",
    "full_image_labels",
    "nearby_non_manhole_labels",
    "prefilter_status",
    "proposed_label",
    "human_decision",
    "reviewer_notes",
)


def repository_relative(path: Path, repository_root: Path) -> str:
    """Return a repository-relative path and reject outside paths."""
    try:
        return path.resolve().relative_to(repository_root.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(f"Path is outside the repository: {path}") from error


def square_crop(
    box: Iterable[float],
    image_width: int,
    image_height: int,
    context_factor: float = 2.5,
    minimum_side: int = 96,
) -> tuple[int, int, int, int]:
    """Create a square context crop that stays inside the image."""
    x, y, width, height = map(float, box)
    if width <= 0 or height <= 0:
        raise ValueError(f"Non-positive target box: {list(box)}")
    if image_width <= 0 or image_height <= 0:
        raise ValueError("Image dimensions must be positive")
    side = min(
        max(int(math.ceil(max(width, height) * context_factor)), minimum_side),
        image_width,
        image_height,
    )
    center_x = x + width / 2
    center_y = y + height / 2
    left = max(0, min(int(round(center_x - side / 2)), image_width - side))
    top = max(0, min(int(round(center_y - side / 2)), image_height - side))
    return left, top, left + side, top + side


def intersection_area(box: Iterable[float], crop: tuple[int, int, int, int]) -> float:
    """Return the overlap area between an xywh box and an xyxy crop."""
    x, y, width, height = map(float, box)
    left, top, right, bottom = crop
    return max(0.0, min(x + width, right) - max(x, left)) * max(
        0.0, min(y + height, bottom) - max(y, top)
    )


def nearby_non_manhole_labels(
    labels: list[str],
    boxes: list[list[float]],
    target_index: int,
    crop: tuple[int, int, int, int],
) -> tuple[str, ...]:
    """Find other labelled conditions that materially enter the crop."""
    crop_area = max((crop[2] - crop[0]) * (crop[3] - crop[1]), 1)
    nearby: set[str] = set()
    for index, (label, box) in enumerate(zip(labels, boxes)):
        if index == target_index or label == "manhole_cover":
            continue
        overlap = intersection_area(box, crop)
        if overlap <= 0:
            continue
        other_area = max(float(box[2]) * float(box[3]), 1.0)
        if overlap / other_area >= 0.10 or overlap / crop_area >= 0.02:
            nearby.add(label)
    return tuple(sorted(nearby))


def build_candidates(
    repository_root: Path,
    annotations_path: Path,
    images_root: Path,
    minimum_target_side: float = 12.0,
) -> list[dict[str, Any]]:
    """Build one record for every source-training manhole box."""
    if annotations_path.name != REQUIRED_ANNOTATION_NAME:
        raise ValueError(
            f"Only the SVRDD source training annotations are allowed; expected {REQUIRED_ANNOTATION_NAME}"
        )
    if not annotations_path.is_file():
        raise FileNotFoundError(f"Missing annotations: {annotations_path}")
    records: list[dict[str, Any]] = []
    with annotations_path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            try:
                item = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON on line {line_number}") from error
            labels = [str(value) for value in item.get("objects", {}).get("v2_labels", [])]
            boxes = item.get("objects", {}).get("bbox", [])
            if len(labels) != len(boxes):
                raise ValueError(f"Label and box counts differ on line {line_number}")
            image_id = str(item.get("image_id", "")).strip()
            file_name = str(item.get("file_name", "")).strip()
            width = int(item.get("width", 0))
            height = int(item.get("height", 0))
            if not image_id or not file_name or width <= 0 or height <= 0:
                raise ValueError(f"Missing image metadata on line {line_number}")
            image_path = images_root / Path(file_name)
            if not image_path.is_file():
                raise FileNotFoundError(f"Missing source image: {image_path}")
            for object_index, (label, box) in enumerate(zip(labels, boxes)):
                if label != "manhole_cover":
                    continue
                if len(box) != 4:
                    raise ValueError(f"Invalid target box on line {line_number}: {box}")
                crop = square_crop(box, width, height)
                nearby = nearby_non_manhole_labels(labels, boxes, object_index, crop)
                minimum_side = min(float(box[2]), float(box[3]))
                if minimum_side < minimum_target_side:
                    status = "hold_target_too_small"
                elif nearby:
                    status = "hold_nearby_other_condition"
                else:
                    status = "review_candidate_clear_context"
                records.append(
                    {
                        "candidate_id": f"svrdd::train::{image_id}::manhole::{object_index:03d}",
                        "source_image_id": image_id,
                        "region": str(item.get("region", "")),
                        "source_image_path": repository_relative(image_path, repository_root),
                        "image_path": image_path,
                        "target_index": object_index,
                        "target_box": tuple(map(float, box)),
                        "all_boxes": [tuple(map(float, value)) for value in boxes],
                        "all_labels": labels,
                        "crop_box": crop,
                        "target_min_side_px": minimum_side,
                        "full_image_labels": tuple(sorted(set(labels))),
                        "nearby_non_manhole_labels": nearby,
                        "prefilter_status": status,
                    }
                )
    return records


def select_stratified_sample(
    records: list[dict[str, Any]],
    sample_size: int,
    seed: int,
) -> list[dict[str, Any]]:
    """Select a repeatable, region-balanced sample from review candidates."""
    if sample_size <= 0:
        raise ValueError("sample_size must be positive")
    eligible = [record for record in records if record["prefilter_status"] == "review_candidate_clear_context"]
    if sample_size > len(eligible):
        raise ValueError(f"Requested {sample_size} samples but only {len(eligible)} are eligible")
    by_region: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in eligible:
        by_region[str(record["region"])].append(record)
    random_generator = random.Random(seed)
    for region_records in by_region.values():
        region_records.sort(key=lambda record: str(record["candidate_id"]))
        random_generator.shuffle(region_records)
    selected: list[dict[str, Any]] = []
    regions = sorted(by_region)
    while len(selected) < sample_size:
        made_progress = False
        for region in regions:
            if by_region[region] and len(selected) < sample_size:
                selected.append(by_region[region].pop())
                made_progress = True
        if not made_progress:
            break
    return selected


def _fit_image(image: Image.Image, size: tuple[int, int], allow_enlarge: bool) -> Image.Image:
    """Fit an image inside a preview area without changing its proportions."""
    result = image.copy()
    scale = min(size[0] / result.width, size[1] / result.height)
    if not allow_enlarge:
        scale = min(scale, 1.0)
    new_size = (max(1, int(result.width * scale)), max(1, int(result.height * scale)))
    resampling = Image.Resampling.NEAREST if scale > 1 else Image.Resampling.LANCZOS
    return result.resize(new_size, resampling)


def create_preview(record: dict[str, Any], output_path: Path) -> None:
    """Create a context-and-crop preview; raw source images remain untouched."""
    with Image.open(record["image_path"]) as opened:
        source = opened.convert("RGB")
    context = source.copy()
    context_draw = ImageDraw.Draw(context)
    for index, (label, box) in enumerate(zip(record["all_labels"], record["all_boxes"])):
        x, y, width, height = box
        color = (0, 210, 80) if index == record["target_index"] else (220, 50, 50)
        context_draw.rectangle((x, y, x + width, y + height), outline=color, width=4)
    crop_box = record["crop_box"]
    crop_image = source.crop(crop_box)
    crop_draw = ImageDraw.Draw(crop_image)
    target_x, target_y, target_width, target_height = record["target_box"]
    crop_draw.rectangle(
        (
            target_x - crop_box[0],
            target_y - crop_box[1],
            target_x + target_width - crop_box[0],
            target_y + target_height - crop_box[1],
        ),
        outline=(0, 210, 80),
        width=max(2, crop_image.width // 80),
    )
    context = _fit_image(context, (330, 220), allow_enlarge=False)
    crop_image = _fit_image(crop_image, (240, 220), allow_enlarge=True)
    canvas = Image.new("RGB", (620, 270), "white")
    canvas.paste(context, (10 + (330 - context.width) // 2, 25 + (220 - context.height) // 2))
    canvas.paste(crop_image, (370 + (240 - crop_image.width) // 2, 25 + (220 - crop_image.height) // 2))
    draw = ImageDraw.Draw(canvas)
    draw.text((10, 6), "Full image context (green target; red other boxes)", fill="black")
    draw.text((370, 6), "Proposed manhole crop", fill="black")
    draw.text((10, 250), f"Region: {record['region']} | Target minimum side: {record['target_min_side_px']:.0f}px", fill="black")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG", optimize=True)


def write_review_manifest(
    selected: list[dict[str, Any]],
    output_path: Path,
    previews_dir: Path,
) -> list[dict[str, str]]:
    """Create preview files and a pending human-review manifest."""
    rows: list[dict[str, str]] = []
    for sequence, record in enumerate(selected, start=1):
        sample_id = f"manhole_{sequence:03d}"
        preview_path = previews_dir / f"{sample_id}.png"
        create_preview(record, preview_path)
        rows.append(
            {
                "sample_id": sample_id,
                "candidate_id": str(record["candidate_id"]),
                "source_image_id": str(record["source_image_id"]),
                "region": str(record["region"]),
                "source_image_path": str(record["source_image_path"]),
                "preview_file": preview_path.name,
                "target_box_xywh": ",".join(f"{value:.3f}" for value in record["target_box"]),
                "crop_box_xyxy": ",".join(str(value) for value in record["crop_box"]),
                "target_min_side_px": f"{record['target_min_side_px']:.3f}",
                "full_image_labels": ";".join(record["full_image_labels"]),
                "nearby_non_manhole_labels": ";".join(record["nearby_non_manhole_labels"]),
                "prefilter_status": str(record["prefilter_status"]),
                "proposed_label": "manhole_cover",
                "human_decision": "pending",
                "reviewer_notes": "",
            }
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def summarize(records: list[dict[str, Any]], selected: list[dict[str, Any]]) -> dict[str, Any]:
    """Create data-review evidence, not model performance evidence."""
    return {
        "source_split": "train",
        "manhole_boxes_found": len(records),
        "prefilter_counts": dict(sorted(Counter(str(record["prefilter_status"]) for record in records).items())),
        "eligible_by_region": dict(
            sorted(
                Counter(
                    str(record["region"])
                    for record in records
                    if record["prefilter_status"] == "review_candidate_clear_context"
                ).items()
            )
        ),
        "review_sample_records": len(selected),
        "review_sample_by_region": dict(sorted(Counter(str(record["region"]) for record in selected).items())),
        "human_review_status": "pending",
        "training_status": "not_approved",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--images-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--previews-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--sample-size", type=int, default=60)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    records = build_candidates(args.repo_root, args.annotations, args.images_root)
    selected = select_stratified_sample(records, args.sample_size, args.seed)
    write_review_manifest(selected, args.manifest, args.previews_dir)
    report = summarize(records, selected)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Saved review manifest: {args.manifest}")
    print(f"Saved preview images: {args.previews_dir}")


if __name__ == "__main__":
    main()
