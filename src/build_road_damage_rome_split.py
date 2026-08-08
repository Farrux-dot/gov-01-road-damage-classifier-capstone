"""Build the duplicate-free, capture-group-aware Version 2 binary image split."""
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from collections import Counter, defaultdict
from pathlib import Path


# These six groups are the only conservative capture-group evidence supplied by
# the filenames. They are assigned as whole groups to prevent image-level
# random splitting from leaking likely neighbouring video frames.
SPLIT_GROUPS = {
    "train": {"20250218", "20250219"},
    "validation": {"unknown_capture_group"},
    "test": {"20250216", "20250223", "20250226"},
}
EXPECTED_LABELS = {"Pothole", "No_pothole"}


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def group_to_split() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for split, groups in SPLIT_GROUPS.items():
        for group in groups:
            if group in mapping:
                raise ValueError(f"Group {group} appears in two configured splits.")
            mapping[group] = split
    return mapping


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-data-dir", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--split-summary", type=Path, required=True)
    parser.add_argument("--clean-manifest", type=Path, required=True)
    args = parser.parse_args()

    source_images = args.source_data_dir / "images"
    if not source_images.is_dir():
        raise FileNotFoundError(f"Source image directory not found: {source_images}")
    if not args.source_manifest.is_file():
        raise FileNotFoundError(f"Source manifest not found: {args.source_manifest}")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise FileExistsError(f"Output directory already contains files: {args.output_dir}")

    with args.source_manifest.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    required_columns = {"source_filename", "binary_label", "group_id", "sha256"}
    if not rows or not required_columns.issubset(rows[0]):
        raise ValueError(f"Source manifest must contain {sorted(required_columns)}")

    split_for_group = group_to_split()
    observed_groups = {row["group_id"] for row in rows}
    if observed_groups != set(split_for_group):
        raise ValueError(
            "Observed groups do not exactly match the configured groups. "
            f"Observed: {sorted(observed_groups)}; configured: {sorted(split_for_group)}"
        )

    rows_by_hash: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["binary_label"] not in EXPECTED_LABELS:
            raise ValueError(f"Unexpected binary label: {row['binary_label']}")
        rows_by_hash[row["sha256"]].append(row)

    canonical_rows: list[dict[str, str]] = []
    for digest, duplicate_rows in rows_by_hash.items():
        labels = {row["binary_label"] for row in duplicate_rows}
        if len(labels) != 1:
            raise ValueError(f"Duplicate hash {digest} has inconsistent labels: {labels}")
        canonical_rows.append(min(duplicate_rows, key=lambda row: row["source_filename"]))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    clean_rows: list[dict[str, str]] = []
    split_counts: dict[str, Counter[str]] = {split: Counter() for split in SPLIT_GROUPS}
    hashes_by_split: dict[str, set[str]] = {split: set() for split in SPLIT_GROUPS}

    for row in sorted(canonical_rows, key=lambda item: item["source_filename"]):
        split = split_for_group[row["group_id"]]
        source_path = source_images / row["source_filename"]
        if not source_path.is_file():
            raise FileNotFoundError(f"Manifest image not found: {source_path}")
        if file_digest(source_path) != row["sha256"]:
            raise ValueError(f"Hash mismatch for {source_path}")

        destination = args.output_dir / split / row["binary_label"] / row["source_filename"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        split_counts[split][row["binary_label"]] += 1
        hashes_by_split[split].add(row["sha256"])
        clean_rows.append(
            {
                **row,
                "split": split,
                "derived_path": destination.as_posix(),
            }
        )

    for left_split, left_hashes in hashes_by_split.items():
        for right_split, right_hashes in hashes_by_split.items():
            if left_split >= right_split:
                continue
            overlap = left_hashes & right_hashes
            if overlap:
                raise ValueError(f"Hash overlap between {left_split} and {right_split}: {len(overlap)}")

    args.split_summary.parent.mkdir(parents=True, exist_ok=True)
    with args.split_summary.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=("split", "groups", "total", "No_pothole", "Pothole", "percent_of_clean_pool"))
        writer.writeheader()
        clean_total = len(clean_rows)
        for split in ("train", "validation", "test"):
            total = sum(split_counts[split].values())
            writer.writerow(
                {
                    "split": split,
                    "groups": "|".join(sorted(SPLIT_GROUPS[split])),
                    "total": total,
                    "No_pothole": split_counts[split]["No_pothole"],
                    "Pothole": split_counts[split]["Pothole"],
                    "percent_of_clean_pool": f"{total / clean_total:.4f}",
                }
            )

    args.clean_manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.clean_manifest.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=tuple(clean_rows[0]))
        writer.writeheader()
        writer.writerows(clean_rows)

    print(f"Created clean split at {args.output_dir}")
    for split in ("train", "validation", "test"):
        print(f"{split}: {dict(split_counts[split])}")
    print(f"Unique images retained: {len(clean_rows)}")
    print(f"Duplicate copies excluded: {len(rows) - len(clean_rows)}")
    print("Exact-hash overlap across derived splits: 0")


if __name__ == "__main__":
    main()
