"""Find visually similar V2 split records before images are materialized.

This audit uses a compact difference hash (dHash) to shortlist cross-split
images that may be near duplicates. It does not remove files or alter the
split manifest. Human or later policy review is required before exclusions.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageStat


PAIR_FIELDS = (
    "candidate_id_a",
    "split_a",
    "label_a",
    "source_a",
    "candidate_id_b",
    "split_b",
    "label_b",
    "source_b",
    "hamming_distance",
    "recommended_action",
)


def image_fingerprint(path: Path) -> tuple[int, tuple[int, int], tuple[int, ...]]:
    """Return dHash plus a small brightness thumbnail for a conservative shortlist."""
    with Image.open(path) as image:
        grayscale = image.convert("L").resize((9, 8))
        pixels = list(grayscale.get_flattened_data())
        thumbnail_image = image.convert("L").resize((16, 16))
        thumbnail = tuple(thumbnail_image.get_flattened_data())
        stats = ImageStat.Stat(thumbnail_image)
    value = 0
    for row in range(8):
        start = row * 9
        for column in range(8):
            value = (value << 1) | int(pixels[start + column] > pixels[start + column + 1])
    # Coarse brightness/contrast bins avoid comparing every uniformly dark road.
    coarse = (int(stats.mean[0]) // 8, int(stats.stddev[0]) // 8)
    return value, coarse, thumbnail


def band_values(value: int) -> tuple[int, ...]:
    """Return six fixed bit bands; a distance <=5 pair shares one band."""
    widths = (11, 11, 11, 11, 10, 10)
    bands: list[int] = []
    remaining = 64
    for width in widths:
        remaining -= width
        bands.append((value >> remaining) & ((1 << width) - 1))
    return tuple(bands)


def recommended_action(distance: int) -> str:
    if distance == 0:
        return "holdout_required_same_visual_hash"
    if distance <= 3:
        return "holdout_required_likely_near_duplicate"
    return "review_required_possible_near_duplicate"


def thumbnail_mean_absolute_difference(left: tuple[int, ...], right: tuple[int, ...]) -> float:
    """Measure brightness disagreement between two 16 x 16 thumbnails."""
    return sum(abs(first - second) for first, second in zip(left, right)) / len(left)


def candidate_pairs(records: list[dict[str, str]], maximum_distance: int) -> list[dict[str, str]]:
    """Return unique cross-split pairs within the requested dHash distance."""
    buckets: dict[tuple[int, int, int, int], list[int]] = defaultdict(list)
    hashes: list[int] = []
    for index, record in enumerate(records):
        value = int(record["dhash"], 16)
        hashes.append(value)
        mean_bin, contrast_bin = record["coarse"]
        for band_index, band in enumerate(band_values(value)):
            buckets[(band_index, band, mean_bin, contrast_bin)].append(index)

    pair_map: dict[tuple[str, str], dict[str, str]] = {}
    for bucket_key, members in buckets.items():
        band_index = bucket_key[0]
        for offset, first in enumerate(members):
            for second in members[offset + 1 :]:
                # A pair can share more than one band. Compare it only in the
                # first shared band, without keeping a potentially huge set of
                # all non-matching pair keys in memory.
                left_bands = band_values(hashes[first])
                right_bands = band_values(hashes[second])
                if any(left_bands[index] == right_bands[index] for index in range(band_index)):
                    continue
                left, right = records[first], records[second]
                if left["split"] == right["split"]:
                    continue
                distance = (hashes[first] ^ hashes[second]).bit_count()
                if distance > maximum_distance:
                    continue
                if thumbnail_mean_absolute_difference(left["thumbnail"], right["thumbnail"]) > 8.0:
                    continue
                pair_key = tuple(sorted((left["candidate_id"], right["candidate_id"])))
                pair_map[pair_key] = {
                    "candidate_id_a": left["candidate_id"],
                    "split_a": left["split"],
                    "label_a": left["proposed_multiclass_label"],
                    "source_a": left["source_id"],
                    "candidate_id_b": right["candidate_id"],
                    "split_b": right["split"],
                    "label_b": right["proposed_multiclass_label"],
                    "source_b": right["source_id"],
                    "hamming_distance": str(distance),
                    "recommended_action": recommended_action(distance),
                }
    return sorted(pair_map.values(), key=lambda item: (int(item["hamming_distance"]), item["candidate_id_a"], item["candidate_id_b"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--pairs-output", type=Path, required=True)
    parser.add_argument("--report-output", type=Path, required=True)
    parser.add_argument("--maximum-distance", type=int, default=5)
    args = parser.parse_args()
    if not 0 <= args.maximum_distance <= 64:
        raise ValueError("maximum-distance must be between 0 and 64")

    manifest = args.manifest.resolve()
    repository_root = manifest.parents[1]
    with manifest.open(newline="", encoding="utf-8-sig") as file:
        records = list(csv.DictReader(file))

    for record in records:
        image_path = (repository_root / record["source_image_path"]).resolve()
        try:
            image_path.relative_to(repository_root)
        except ValueError as error:
            raise ValueError(f"Path outside repository: {record['source_image_path']}") from error
        if not image_path.is_file():
            raise FileNotFoundError(f"Missing manifest image: {record['source_image_path']}")
        value, coarse, thumbnail = image_fingerprint(image_path)
        record["dhash"] = f"{value:016x}"
        record["coarse"] = coarse
        record["thumbnail"] = thumbnail

    pairs = candidate_pairs(records, args.maximum_distance)
    args.pairs_output.parent.mkdir(parents=True, exist_ok=True)
    with args.pairs_output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PAIR_FIELDS)
        writer.writeheader()
        writer.writerows(pairs)

    report = {
        "audit": "cross_split_dhash_near_duplicate_shortlist",
        "manifest": manifest.relative_to(repository_root).as_posix(),
        "records_hashed": len(records),
        "maximum_hamming_distance": args.maximum_distance,
        "cross_split_suspicious_pair_count": len(pairs),
        "pairs_by_distance": dict(sorted(Counter(item["hamming_distance"] for item in pairs).items(), key=lambda item: int(item[0]))),
        "pairs_requiring_holdout": sum(item["recommended_action"].startswith("holdout") for item in pairs),
        "decision": "No split assignments were changed. Review or policy handling is required before materialization if suspicious pairs exist.",
    }
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Images hashed: {len(records)}")
    print(f"Cross-split suspicious pairs: {len(pairs)}")
    print(f"Pairs requiring holdout: {report['pairs_requiring_holdout']}")
    print(f"Pairs CSV: {args.pairs_output}")
    print(f"Report JSON: {args.report_output}")


if __name__ == "__main__":
    main()
