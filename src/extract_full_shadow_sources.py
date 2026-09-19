"""Extract the original shadow images from full SRD and ISTD Parquet downloads.

The source datasets are stored as Parquet records.  This tool creates ordinary
JPG/PNG files under ``data/raw/v2`` so a human can inspect them in File
Explorer.  It extracts only the original shadow image, never alters it, and
does not add records to the V2 candidate inventory or create a model split.
"""

from __future__ import annotations

import argparse
import csv
import io
from pathlib import Path

import pyarrow.parquet as pq
from PIL import Image


SOURCES = {
    "srd": Path("data/raw/v2/srd_full_hf"),
    "istd": Path("data/raw/v2/istd_full_hf"),
}


def relative_to_repo(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def safe_filename(value: str) -> str:
    """Keep the source filename readable while preventing path traversal."""
    return Path(value).name.replace(" ", "_")


def verify_image(image_bytes: bytes, source_name: str) -> None:
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image.verify()
    except Exception as error:  # Pillow raises format-specific exceptions.
        raise ValueError(f"Unreadable source image: {source_name}") from error


def extract_source(repo_root: Path, source_key: str) -> tuple[int, Path]:
    source_root = repo_root / SOURCES[source_key]
    data_root = source_root / "data"
    if not data_root.is_dir():
        raise FileNotFoundError(f"Missing downloaded Parquet folder: {data_root}")

    output_root = source_root / "extracted_shadow_images"
    manifest_path = source_root / "extracted_shadow_image_manifest.csv"
    parquet_files = sorted(data_root.glob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No Parquet files found in: {data_root}")

    rows: list[dict[str, str]] = []
    record_index = 0
    for parquet_path in parquet_files:
        split = parquet_path.name.split("-", maxsplit=1)[0]
        parquet = pq.ParquetFile(parquet_path)
        for batch in parquet.iter_batches(columns=["image", "filename"], batch_size=64):
            for record in batch.to_pylist():
                filename = safe_filename(record["filename"])
                image_bytes = record["image"]["bytes"]
                if not image_bytes:
                    raise ValueError(f"Missing image bytes: {parquet_path.name} / {filename}")
                verify_image(image_bytes, filename)

                output_name = f"{record_index:05d}__{filename}"
                output_path = output_root / split / output_name
                output_path.parent.mkdir(parents=True, exist_ok=True)
                if output_path.exists() and output_path.read_bytes() != image_bytes:
                    raise ValueError(f"Existing extracted file differs: {output_path}")
                if not output_path.exists():
                    output_path.write_bytes(image_bytes)

                rows.append(
                    {
                        "source_dataset": source_key.upper(),
                        "source_split": split,
                        "source_parquet": relative_to_repo(repo_root, parquet_path),
                        "source_filename": filename,
                        "source_record_index": str(record_index),
                        "image_path": relative_to_repo(repo_root, output_path),
                        "inventory_status": "not_integrated_pending_audit",
                    }
                )
                record_index += 1

    with manifest_path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return record_index, manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=sorted(SOURCES), required=True)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    count, manifest_path = extract_source(repo_root, args.source)
    print(f"Extracted {count} {args.source.upper()} shadow images")
    print(f"Manifest: {relative_to_repo(repo_root, manifest_path)}")
    print("Inventory status: not integrated; full audit and deduplication still required.")


if __name__ == "__main__":
    main()
