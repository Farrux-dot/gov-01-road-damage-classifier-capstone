"""Materialize the approved V2 multi-label split without changing raw data.

This tool copies each source image exactly once into ignored processed-data
folders, writes one label CSV per split, and verifies that every copied byte
stream has the SHA-256 value recorded in the prior image audit.  It refuses to
overwrite an existing target.  It never edits or removes source images.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any, BinaryIO, Iterator

if __package__:
    from src.build_v2_multilabel_coverage_manifest import ACTIVE_CONDITIONS
else:
    from build_v2_multilabel_coverage_manifest import ACTIVE_CONDITIONS  # type: ignore[no-redef]


SPLITS = ("train", "validation", "test")
SAFETY_BUFFER_BYTES = 1024 * 1024 * 1024
LABEL_FIELDS = (
    "record_id",
    "source_dataset",
    "source_image_reference",
    "materialized_image",
    "sha256",
) + tuple(
    field for condition in ACTIVE_CONDITIONS for field in (f"{condition}_known", f"{condition}_present")
)


def _read_rows(path: Path, required_fields: set[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        fields = set(reader.fieldnames or ())
        if not required_fields.issubset(fields):
            raise ValueError(f"{path.name} must contain: {sorted(required_fields)}")
        return list(reader)


def _index_unique(rows: list[dict[str, str]], key: str, name: str) -> dict[str, dict[str, str]]:
    result = {row[key]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"{name} has duplicate {key} values")
    return result


def _suffix(reference: str) -> str:
    source = reference.split("#", 1)[1] if "#" in reference else reference
    suffix = Path(source).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png"}:
        raise ValueError(f"Unsupported image suffix in source reference: {reference}")
    return suffix


def _source_size(reference: str) -> int:
    if "#" not in reference:
        return Path(reference).stat().st_size
    archive_path, member = reference.split("#", 1)
    with zipfile.ZipFile(archive_path) as archive:
        return archive.getinfo(member).file_size


@contextlib.contextmanager
def _open_source(reference: str) -> Iterator[BinaryIO]:
    if "#" not in reference:
        with Path(reference).open("rb") as source:
            yield source
        return
    archive_path, member = reference.split("#", 1)
    with zipfile.ZipFile(archive_path) as archive, archive.open(member) as source:
        yield source


def _target_parent(path: Path) -> Path:
    candidate = path.parent
    while not candidate.exists():
        candidate = candidate.parent
    return candidate


def prepare_materialization(
    manifest_rows: list[dict[str, str]], plan_rows: list[dict[str, str]], audit_rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    """Join approved inputs and return deterministic copy instructions."""
    manifest = _index_unique(manifest_rows, "record_id", "Manifest")
    plan = _index_unique(plan_rows, "record_id", "Split plan")
    audit = _index_unique(audit_rows, "record_id", "Image audit")
    if set(manifest) != set(plan) or set(manifest) != set(audit):
        raise ValueError("Manifest, split plan, and image audit must contain the same record IDs")
    prepared: list[dict[str, str]] = []
    names: set[str] = set()
    for record_id in sorted(manifest):
        source, assignment, audited = manifest[record_id], plan[record_id], audit[record_id]
        if assignment["planned_split"] not in SPLITS:
            raise ValueError(f"{record_id} has invalid planned split: {assignment['planned_split']}")
        if audited["readable"] != "yes" or not audited["sha256"]:
            raise ValueError(f"{record_id} was not readable in the prior image audit")
        if source["image_reference"] != audited["image_reference"]:
            raise ValueError(f"{record_id} image reference differs from the prior audit")
        if source["source_dataset"] != assignment["source_dataset"]:
            raise ValueError(f"{record_id} source name differs between manifest and split plan")
        file_name = f"{hashlib.sha256(record_id.encode('utf-8')).hexdigest()[:24]}{_suffix(source['image_reference'])}"
        if file_name in names:
            raise ValueError(f"Generated duplicate materialized filename for {record_id}")
        names.add(file_name)
        prepared.append(
            {
                "record_id": record_id,
                "planned_split": assignment["planned_split"],
                "source_dataset": source["source_dataset"],
                "source_image_reference": source["image_reference"],
                "sha256": audited["sha256"],
                "file_name": file_name,
                **{field: source[field] for condition in ACTIVE_CONDITIONS for field in (f"{condition}_known", f"{condition}_present")},
            }
        )
    return prepared


def estimate_required_bytes(prepared: list[dict[str, str]]) -> int:
    """Return output image bytes without copying or extracting any source image."""
    return sum(_source_size(row["source_image_reference"]) for row in prepared)


def _copy_verified(reference: str, destination: Path, expected_sha256: str) -> None:
    temporary = destination.with_name(f"{destination.name}.partial")
    digest = hashlib.sha256()
    with _open_source(reference) as source, temporary.open("wb") as output:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            output.write(block)
            digest.update(block)
    if digest.hexdigest() != expected_sha256:
        raise ValueError(f"Checksum changed while copying: {reference}")
    temporary.replace(destination)


def _write_labels(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=LABEL_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def materialize(prepared: list[dict[str, str]], target: Path) -> dict[str, Any]:
    """Copy the approved records into a new target and write split label files."""
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite existing materialization target: {target}")
    estimated_bytes = estimate_required_bytes(prepared)
    free_bytes = shutil.disk_usage(_target_parent(target)).free
    required_bytes = estimated_bytes + SAFETY_BUFFER_BYTES
    if free_bytes < required_bytes:
        raise OSError(
            f"Insufficient free disk space: need at least {required_bytes} bytes including safety buffer, have {free_bytes}"
        )
    target.mkdir(parents=True)
    label_rows: dict[str, list[dict[str, str]]] = {split: [] for split in SPLITS}
    for index, row in enumerate(prepared, start=1):
        split = row["planned_split"]
        image_path = target / split / "images" / row["file_name"]
        image_path.parent.mkdir(parents=True, exist_ok=True)
        _copy_verified(row["source_image_reference"], image_path, row["sha256"])
        label_rows[split].append(
            {
                "record_id": row["record_id"],
                "source_dataset": row["source_dataset"],
                "source_image_reference": row["source_image_reference"],
                "materialized_image": str(Path("images") / row["file_name"]),
                "sha256": row["sha256"],
                **{field: row[field] for condition in ACTIVE_CONDITIONS for field in (f"{condition}_known", f"{condition}_present")},
            }
        )
        if index % 500 == 0:
            print(f"Copied and verified {index}/{len(prepared)} images", flush=True)
    for split in SPLITS:
        split_root = target / split
        _write_labels(split_root / "labels.csv", sorted(label_rows[split], key=lambda row: row["record_id"]))
    summary = {
        "materialization": "v2_multilabel_safe_split",
        "records": len(prepared),
        "estimated_image_bytes": estimated_bytes,
        "splits": {split: len(rows) for split, rows in label_rows.items()},
        "decision": "Source images were copied byte-for-byte with checksum verification. Raw sources were not changed. The test split remains separate for one final evaluation after model selection.",
    }
    (target / "materialization_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--split-plan", type=Path, required=True)
    parser.add_argument("--image-audit", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    manifest_required = {"record_id", "source_dataset", "image_reference"} | {
        f"{condition}_{field}" for condition in ACTIVE_CONDITIONS for field in ("known", "present")
    }
    prepared = prepare_materialization(
        _read_rows(args.manifest, manifest_required),
        _read_rows(args.split_plan, {"record_id", "source_dataset", "planned_split"}),
        _read_rows(args.image_audit, {"record_id", "image_reference", "readable", "sha256"}),
    )
    estimated_bytes = estimate_required_bytes(prepared)
    free_bytes = shutil.disk_usage(_target_parent(args.target)).free
    print(f"Planned images: {len(prepared)}")
    print(f"Estimated copied image bytes: {estimated_bytes}")
    print(f"Available bytes: {free_bytes}")
    if args.dry_run:
        print("Dry run complete: no files were written.")
        return
    summary = materialize(prepared, args.target)
    print(f"Materialized and checksum-verified records: {summary['records']}")


if __name__ == "__main__":
    main()
