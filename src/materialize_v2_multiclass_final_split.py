"""Materialize the approved V2 multi-class split without modifying raw data."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path


ACTIVE_SPLITS = {"train", "validation", "protected_test"}
OUTPUT_FIELDS = [
    "candidate_id",
    "source_image_path",
    "proposed_multiclass_label",
    "split_group_id",
    "split",
    "source_sha256",
    "materialized_image_path",
    "materialized_sha256",
    "verification_status",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_source_path(repository_root: Path, relative_path: str) -> Path:
    path = (repository_root / relative_path).resolve()
    try:
        path.relative_to(repository_root.resolve())
    except ValueError as exc:
        raise ValueError(f"Source path escapes repository: {relative_path}") from exc
    return path


def destination_for(row: dict[str, str], output_root: Path) -> Path:
    suffix = Path(row["source_image_path"]).suffix.lower() or ".img"
    safe_name = hashlib.sha256(row["candidate_id"].encode("utf-8")).hexdigest()[:24]
    return output_root / row["split"] / row["proposed_multiclass_label"] / f"{safe_name}{suffix}"


def load_active_rows(manifest_path: Path) -> list[dict[str, str]]:
    with manifest_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    required = {
        "candidate_id", "source_image_path", "sha256", "proposed_multiclass_label",
        "split_group_id", "split",
    }
    missing = required - set(rows[0] if rows else [])
    if missing:
        raise ValueError(f"Manifest lacks required columns: {sorted(missing)}")
    active = [row for row in rows if row["split"] in ACTIVE_SPLITS]
    if len({row["candidate_id"] for row in active}) != len(active):
        raise ValueError("Active manifest rows must have unique candidate IDs.")
    if any(not row["proposed_multiclass_label"] for row in active):
        raise ValueError("Active manifest rows require a proposed primary label.")
    return active


def ensure_output_root_is_safe(output_root: Path, resume: bool) -> None:
    if output_root.exists() and any(output_root.iterdir()) and not resume:
        raise FileExistsError(
            f"Refusing to write into non-empty output directory without --resume: {output_root}"
        )


def repository_relative(path: Path, repository_root: Path) -> str:
    return path.resolve().relative_to(repository_root.resolve()).as_posix()


def materialize(
    rows: list[dict[str, str]], repository_root: Path, output_root: Path, dry_run: bool,
    resume: bool,
) -> list[dict[str, str]]:
    output_rows: list[dict[str, str]] = []
    destinations: set[Path] = set()
    for row in rows:
        source = safe_source_path(repository_root, row["source_image_path"])
        destination = destination_for(row, output_root)
        if destination in destinations:
            raise ValueError(f"Destination collision: {destination}")
        destinations.add(destination)
        if not source.is_file():
            raise FileNotFoundError(f"Missing source image: {source}")
        source_hash = sha256_file(source)
        if source_hash != row["sha256"]:
            raise ValueError(f"Source hash mismatch: {source}")

        output_row = {
            "candidate_id": row["candidate_id"],
            "source_image_path": row["source_image_path"],
            "proposed_multiclass_label": row["proposed_multiclass_label"],
            "split_group_id": row["split_group_id"],
            "split": row["split"],
            "source_sha256": source_hash,
            "materialized_image_path": repository_relative(destination, repository_root),
            "materialized_sha256": "",
            "verification_status": "planned" if dry_run else "",
        }
        if not dry_run and destination.exists():
            if not resume:
                raise FileExistsError(f"Refusing to overwrite existing file: {destination}")
            copied_hash = sha256_file(destination)
            if copied_hash != source_hash:
                raise ValueError(f"Existing destination hash mismatch: {destination}")
            output_row["materialized_sha256"] = copied_hash
            output_row["verification_status"] = "existing_hash_matches_source"
        elif not dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(destination.name + ".partial")
            try:
                shutil.copy2(source, temporary)
                copied_hash = sha256_file(temporary)
                if copied_hash != source_hash:
                    raise ValueError(f"Copied hash mismatch: {destination}")
                temporary.replace(destination)
            except Exception:
                temporary.unlink(missing_ok=True)
                raise
            output_row["materialized_sha256"] = copied_hash
            output_row["verification_status"] = "copied_hash_matches_source"
        output_rows.append(output_row)
    return output_rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Verify matching existing copies and continue.")
    args = parser.parse_args()

    root = args.repository_root.resolve()
    rows = load_active_rows(args.manifest)
    ensure_output_root_is_safe(args.output_root, args.resume)
    output_rows = materialize(rows, root, args.output_root, args.dry_run, args.resume)
    if not args.dry_run:
        write_csv(args.output_manifest, output_rows)
    report = {
        "manifest": repository_relative(args.manifest, root),
        "output_root": repository_relative(args.output_root, root),
        "dry_run": args.dry_run,
        "active_records": len(rows),
        "split_counts": dict(Counter(row["split"] for row in rows)),
        "label_counts": dict(Counter(row["proposed_multiclass_label"] for row in rows)),
        "verified_copies": sum(
            row["verification_status"] == "copied_hash_matches_source" for row in output_rows
        ),
        "verified_existing_copies": sum(
            row["verification_status"] == "existing_hash_matches_source" for row in output_rows
        ),
    }
    if not args.dry_run:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
