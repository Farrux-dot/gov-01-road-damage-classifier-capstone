"""Create an upload-ready ZIP from the verified V2 N-RDD2024 expansion split.

The source dataset is read only. The archive contains the top-level dataset
folder so Colab can extract it directly into its temporary working directory.
"""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


def package(source: Path, archive_path: Path) -> int:
    if not source.is_dir():
        raise FileNotFoundError(f"Missing source dataset directory: {source}")
    if archive_path.exists():
        raise FileExistsError(f"Refusing to overwrite archive: {archive_path}")
    files = sorted(path for path in source.rglob("*") if path.is_file())
    if not files:
        raise ValueError(f"Source dataset contains no files: {source}")
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        for index, file_path in enumerate(files, start=1):
            archive.write(file_path, file_path.relative_to(source.parent))
            if index % 500 == 0:
                print(f"Archived {index}/{len(files)}", flush=True)
    print(f"Archive complete: {archive_path}")
    return len(files)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    count = package(args.source, args.archive)
    print(f"Archived files: {count}")


if __name__ == "__main__":
    main()
