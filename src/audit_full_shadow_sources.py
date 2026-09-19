"""Audit all downloaded SRD and ISTD shadow-removal records.

The audit verifies every Parquet image/mask/target triplet and writes only
traceable metadata. It does not add the records to the final V2 candidate
inventory, create a split, or train a model. SRD and ISTD contain general
shadow-removal scenes, so road relevance remains a separate human decision.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow.parquet as pq
from PIL import Image


SOURCES = {
    "srd": {
        "root": Path("data/raw/v2/srd_full_hf"),
        "dataset_id": "Donghyun99/SRD (unofficial Hugging Face mirror)",
        "source_url": "https://huggingface.co/datasets/Donghyun99/SRD",
        "readme_license": "MIT stated in local mirror README; original-source provenance still requires confirmation.",
    },
    "istd": {
        "root": Path("data/raw/v2/istd_full_hf"),
        "dataset_id": "Donghyun99/ISTD (unofficial Hugging Face mirror)",
        "source_url": "https://huggingface.co/datasets/Donghyun99/ISTD",
        "readme_license": "MIT stated in local mirror README; original-source provenance still requires confirmation.",
    },
}
FIELDS = (
    "audit_id",
    "source_key",
    "source_dataset",
    "source_url",
    "source_split",
    "source_parquet",
    "source_record_index",
    "source_filename",
    "source_image_path",
    "width",
    "height",
    "image_sha256",
    "mask_sha256",
    "target_sha256",
    "shadow_mask_coverage",
    "exact_image_duplicate_group_size",
    "audit_status",
    "road_context_status",
    "training_eligibility",
    "license_note",
)


def relative_to_repo(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def image_info(image_bytes: bytes, record_name: str) -> tuple[int, int]:
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image.verify()
        with Image.open(io.BytesIO(image_bytes)) as image:
            return image.size
    except Exception as error:
        raise ValueError(f"Unreadable image bytes for {record_name}") from error


def mask_coverage(mask_bytes: bytes, record_name: str) -> float:
    """Return the share of non-black pixels in a verified shadow mask."""
    try:
        with Image.open(io.BytesIO(mask_bytes)) as image:
            image.verify()
        with Image.open(io.BytesIO(mask_bytes)) as image:
            pixels = list(image.convert("L").get_flattened_data())
    except Exception as error:
        raise ValueError(f"Unreadable mask bytes for {record_name}") from error
    if not pixels:
        raise ValueError(f"Empty mask for {record_name}")
    return round(sum(value > 0 for value in pixels) / len(pixels), 6)


def audit_source(repo_root: Path, source_key: str) -> tuple[list[dict[str, str]], dict[str, object]]:
    source = SOURCES[source_key]
    source_root = repo_root / source["root"]
    data_root = source_root / "data"
    image_root = source_root / "extracted_shadow_images"
    parquet_files = sorted(data_root.glob("*.parquet"))
    if not parquet_files or not image_root.is_dir():
        raise FileNotFoundError(f"Downloaded {source_key.upper()} data is incomplete")

    rows: list[dict[str, str]] = []
    hashes: defaultdict[str, list[int]] = defaultdict(list)
    record_index = 0
    for parquet_path in parquet_files:
        split = parquet_path.name.split("-", maxsplit=1)[0]
        parquet = pq.ParquetFile(parquet_path)
        for batch in parquet.iter_batches(columns=["image", "mask", "target", "filename"], batch_size=64):
            for record in batch.to_pylist():
                filename = Path(record["filename"]).name
                image_bytes = record["image"].get("bytes")
                mask_bytes = record["mask"].get("bytes")
                target_bytes = record["target"].get("bytes")
                if not image_bytes or not mask_bytes or not target_bytes:
                    raise ValueError(f"Missing image, mask, or target bytes: {parquet_path.name} / {filename}")
                width, height = image_info(image_bytes, filename)
                image_info(target_bytes, f"target {filename}")
                coverage = mask_coverage(mask_bytes, filename)
                output_path = image_root / split / f"{record_index:05d}__{filename}"
                if not output_path.is_file():
                    raise FileNotFoundError(f"Expected extracted image is missing: {output_path}")
                image_hash = hashlib.sha256(image_bytes).hexdigest()
                rows.append(
                    {
                        "audit_id": f"{source_key.upper()}_FULL_{record_index + 1:05d}",
                        "source_key": source_key,
                        "source_dataset": source["dataset_id"],
                        "source_url": source["source_url"],
                        "source_split": split,
                        "source_parquet": relative_to_repo(repo_root, parquet_path),
                        "source_record_index": str(record_index),
                        "source_filename": filename,
                        "source_image_path": relative_to_repo(repo_root, output_path),
                        "width": str(width),
                        "height": str(height),
                        "image_sha256": image_hash,
                        "mask_sha256": hashlib.sha256(mask_bytes).hexdigest(),
                        "target_sha256": hashlib.sha256(target_bytes).hexdigest(),
                        "shadow_mask_coverage": str(coverage),
                        "exact_image_duplicate_group_size": "0",  # filled after all records are read
                        "audit_status": "structurally_valid_not_integrated",
                        "road_context_status": "not_individually_road_verified",
                        "training_eligibility": "blocked_pending_provenance_license_and_road_context_filter",
                        "license_note": source["readme_license"],
                    }
                )
                hashes[image_hash].append(len(rows) - 1)
                record_index += 1

    for indexes in hashes.values():
        for index in indexes:
            rows[index]["exact_image_duplicate_group_size"] = str(len(indexes))
    report = {
        "records": len(rows),
        "splits": dict(Counter(row["source_split"] for row in rows)),
        "exact_duplicate_groups": sum(len(indexes) > 1 for indexes in hashes.values()),
        "records_in_exact_duplicate_groups": sum(len(indexes) for indexes in hashes.values() if len(indexes) > 1),
        "mask_coverage_range": [
            min(float(row["shadow_mask_coverage"]) for row in rows),
            max(float(row["shadow_mask_coverage"]) for row in rows),
        ],
    }
    return rows, report


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def run_audit(repo_root: Path) -> dict[str, object]:
    all_rows: list[dict[str, str]] = []
    source_reports: dict[str, object] = {}
    for source_key in SOURCES:
        rows, source_report = audit_source(repo_root, source_key)
        all_rows.extend(rows)
        source_reports[source_key] = source_report
    docs = repo_root / "docs"
    write_csv(docs / "v2_full_shadow_source_audit_manifest.csv", all_rows)
    report = {
        "purpose": "Structural audit only; records are not integrated into the V2 training inventory.",
        "sources": source_reports,
        "total_records": len(all_rows),
        "training_status": "blocked",
        "blockers": [
            "The downloaded datasets are shadow-removal sources, not automatically road-only datasets.",
            "Local mirror README licence statements and original-source provenance require confirmation before training use.",
            "Source test splits remain protected and must not be used for V2 training or tuning.",
            "Road-context suitability requires a separate filter or human review.",
        ],
    }
    (docs / "v2_full_shadow_source_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(run_audit(args.repo_root.resolve()), indent=2))


if __name__ == "__main__":
    main()
