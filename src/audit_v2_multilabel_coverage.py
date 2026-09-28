"""Audit a non-materialized multi-label coverage manifest before preprocessing.

The audit verifies that every referenced image can be read, records exact
content duplicates, and shortlists likely visual duplicates. It never deletes,
copies, relabels, splits, or preprocesses images.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageStat


AUDIT_FIELDS = (
    "record_id",
    "source_dataset",
    "image_reference",
    "readable",
    "width",
    "height",
    "sha256",
    "dhash",
    "error",
)
EXACT_FIELDS = ("exact_duplicate_group_id", "record_id", "source_dataset", "image_reference", "sha256")
NEAR_FIELDS = (
    "record_id_a",
    "source_a",
    "record_id_b",
    "source_b",
    "hamming_distance",
    "recommended_split_policy",
)


def _image_bytes(reference: str) -> bytes:
    """Read a plain image path or an archive-member reference without extraction."""
    if "#" not in reference:
        return Path(reference).read_bytes()
    archive_name, member = reference.split("#", 1)
    if not archive_name or not member:
        raise ValueError(f"Invalid archive image reference: {reference}")
    with zipfile.ZipFile(archive_name) as archive:
        return archive.read(member)


def _fingerprint(image_bytes: bytes) -> tuple[int, tuple[int, int], bytes, int, int]:
    """Return dHash, coarse brightness, thumbnail, and dimensions for one image."""
    with Image.open(io.BytesIO(image_bytes)) as opened:
        opened.verify()
    with Image.open(io.BytesIO(image_bytes)) as opened:
        image = opened.convert("RGB")
        width, height = image.size
        grayscale = image.convert("L").resize((9, 8))
        pixels = list(grayscale.get_flattened_data())
        thumbnail_image = image.convert("L").resize((16, 16))
        thumbnail = bytes(thumbnail_image.get_flattened_data())
        stats = ImageStat.Stat(thumbnail_image)
    value = 0
    for row in range(8):
        start = row * 9
        for column in range(8):
            value = (value << 1) | int(pixels[start + column] > pixels[start + column + 1])
    return value, (int(stats.mean[0]) // 8, int(stats.stddev[0]) // 8), thumbnail, width, height


def _bands(value: int) -> tuple[int, ...]:
    """Six fixed bands guarantee a shared band for hashes at distance five or less."""
    widths = (11, 11, 11, 11, 10, 10)
    result: list[int] = []
    remaining = 64
    for width in widths:
        remaining -= width
        result.append((value >> remaining) & ((1 << width) - 1))
    return tuple(result)


def _thumbnail_difference(first: bytes, second: bytes) -> float:
    return sum(abs(left - right) for left, right in zip(first, second)) / len(first)


def _near_pairs(records: list[dict[str, Any]], maximum_distance: int) -> list[dict[str, str]]:
    """Find conservative likely-near pairs without comparing every possible pair."""
    buckets: dict[tuple[int, int, int, int], list[int]] = defaultdict(list)
    for index, record in enumerate(records):
        for band_index, band in enumerate(_bands(record["dhash_value"])):
            brightness, contrast = record["coarse"]
            buckets[(band_index, band, brightness, contrast)].append(index)
    pairs: dict[tuple[str, str], dict[str, str]] = {}
    for (band_index, _, _, _), members in buckets.items():
        for offset, first_index in enumerate(members):
            first = records[first_index]
            first_bands = _bands(first["dhash_value"])
            for second_index in members[offset + 1 :]:
                second = records[second_index]
                second_bands = _bands(second["dhash_value"])
                if any(first_bands[index] == second_bands[index] for index in range(band_index)):
                    continue
                if first["sha256"] == second["sha256"]:
                    continue
                distance = (first["dhash_value"] ^ second["dhash_value"]).bit_count()
                if distance > maximum_distance or _thumbnail_difference(first["thumbnail"], second["thumbnail"]) > 8.0:
                    continue
                pair_key = tuple(sorted((first["record_id"], second["record_id"])))
                pairs[pair_key] = {
                    "record_id_a": first["record_id"],
                    "source_a": first["source_dataset"],
                    "record_id_b": second["record_id"],
                    "source_b": second["source_dataset"],
                    "hamming_distance": str(distance),
                    "recommended_split_policy": "keep_together_in_one_split",
                }
    return sorted(pairs.values(), key=lambda row: (int(row["hamming_distance"]), row["record_id_a"], row["record_id_b"]))


def audit_rows(rows: list[dict[str, str]], maximum_distance: int = 3) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    """Audit manifest rows and return per-image, exact-group, and near-pair results."""
    audited: list[dict[str, str]] = []
    fingerprinted: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        record_id = row["record_id"]
        source_dataset = row["source_dataset"]
        reference = row["image_reference"]
        try:
            image_bytes = _image_bytes(reference)
            dhash, coarse, thumbnail, width, height = _fingerprint(image_bytes)
            digest = hashlib.sha256(image_bytes).hexdigest()
            audited.append(
                {
                    "record_id": record_id,
                    "source_dataset": source_dataset,
                    "image_reference": reference,
                    "readable": "yes",
                    "width": str(width),
                    "height": str(height),
                    "sha256": digest,
                    "dhash": f"{dhash:016x}",
                    "error": "",
                }
            )
            fingerprinted.append(
                {
                    "record_id": record_id,
                    "source_dataset": source_dataset,
                    "sha256": digest,
                    "dhash_value": dhash,
                    "coarse": coarse,
                    "thumbnail": thumbnail,
                }
            )
        except Exception as error:  # record the failure rather than hiding it
            audited.append(
                {
                    "record_id": record_id,
                    "source_dataset": source_dataset,
                    "image_reference": reference,
                    "readable": "no",
                    "width": "",
                    "height": "",
                    "sha256": "",
                    "dhash": "",
                    "error": f"{type(error).__name__}: {error}",
                }
            )
        if index % 500 == 0:
            print(f"Audited {index}/{len(rows)} images", flush=True)
    by_hash: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in fingerprinted:
        by_hash[record["sha256"]].append(record)
    exact_rows: list[dict[str, str]] = []
    for digest, group in sorted(by_hash.items()):
        if len(group) < 2:
            continue
        group_id = f"exact::{digest[:16]}"
        for record in sorted(group, key=lambda item: item["record_id"]):
            audit_row = next(item for item in audited if item["record_id"] == record["record_id"])
            exact_rows.append(
                {
                    "exact_duplicate_group_id": group_id,
                    "record_id": record["record_id"],
                    "source_dataset": record["source_dataset"],
                    "image_reference": audit_row["image_reference"],
                    "sha256": digest,
                }
            )
    return audited, exact_rows, _near_pairs(fingerprinted, maximum_distance)


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    parser.add_argument("--exact-output", type=Path, required=True)
    parser.add_argument("--near-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    parser.add_argument("--maximum-distance", type=int, default=3)
    args = parser.parse_args()
    if not 0 <= args.maximum_distance <= 5:
        raise ValueError("maximum-distance must be between 0 and 5")
    with args.manifest.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    required = {"record_id", "source_dataset", "image_reference"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"Manifest must contain: {sorted(required)}")
    audited, exact_rows, near_rows = audit_rows(rows, args.maximum_distance)
    _write_csv(args.audit_output, AUDIT_FIELDS, audited)
    _write_csv(args.exact_output, EXACT_FIELDS, exact_rows)
    _write_csv(args.near_output, NEAR_FIELDS, near_rows)
    readable = sum(row["readable"] == "yes" for row in audited)
    summary = {
        "audit": "v2_multilabel_coverage_preprocessing_preflight",
        "records": len(audited),
        "readable_records": readable,
        "unreadable_records": len(audited) - readable,
        "exact_duplicate_group_count": len({row["exact_duplicate_group_id"] for row in exact_rows}),
        "exact_duplicate_record_count": len(exact_rows),
        "likely_near_duplicate_pair_count": len(near_rows),
        "maximum_dhash_distance": args.maximum_distance,
        "decision": "No files were changed. Exact and likely-near duplicate groups must stay together in any future split.",
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Readable images: {readable}/{len(audited)}")
    print(f"Exact duplicate groups: {summary['exact_duplicate_group_count']}")
    print(f"Likely near-duplicate pairs: {len(near_rows)}")


if __name__ == "__main__":
    main()
