"""Record a completed StreetSurfaceVis no-shadow human review.

The workbook is a human-review artifact.  This script reads only the decision
columns, checks every row against the existing V2 inventory, and writes small
traceable CSV manifests.  It does not copy images, change source labels, make
a final split, or train a model.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image


NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
VALID_DECISIONS = {"no_shadow_clear", "shadow_present", "unclear_exclude"}
DECISION_FIELDS = (
    "review_id",
    "candidate_id",
    "source_dataset",
    "source_split",
    "source_record_id",
    "source_image_path",
    "original_source_label",
    "human_decision",
    "reviewer_notes",
    "training_status",
)
MANIFEST_FIELDS = (
    "candidate_id",
    "primary_road_label",
    "verified_condition",
    "review_id",
    "decision",
    "eligibility",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def column_letter(cell_reference: str) -> str:
    match = re.match(r"([A-Z]+)", cell_reference)
    if not match:
        raise ValueError(f"Invalid spreadsheet cell reference: {cell_reference}")
    return match.group(1)


def shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    values: list[str] = []
    for item in root.findall(f"{NS}si"):
        values.append("".join(node.text or "" for node in item.iter(f"{NS}t")))
    return values


def workbook_rows(workbook_path: Path, review_id_prefix: str = "NS-") -> list[dict[str, str]]:
    """Return prefixed review rows from the known first worksheet without Excel packages."""
    with zipfile.ZipFile(workbook_path) as archive:
        strings = shared_strings(archive)
        root = ElementTree.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    rows: list[dict[str, str]] = []
    for row in root.findall(f".//{NS}row"):
        values: dict[str, str] = {}
        for cell in row.findall(f"{NS}c"):
            reference = cell.attrib.get("r", "")
            letter = column_letter(reference)
            value_node = cell.find(f"{NS}v")
            if value_node is None:
                values[letter] = ""
                continue
            value = value_node.text or ""
            if cell.attrib.get("t") == "s":
                values[letter] = strings[int(value)]
            else:
                values[letter] = value
        if values.get("A", "").startswith(review_id_prefix):
            rows.append(values)
    return rows


def verify_image(repo_root: Path, relative_path: str) -> None:
    candidate = (repo_root / relative_path).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError as error:
        raise ValueError(f"Path escapes repository: {relative_path}") from error
    if not candidate.is_file():
        raise FileNotFoundError(f"Reviewed source image is missing: {relative_path}")
    with Image.open(candidate) as image:
        image.verify()


def finalize(repo_root: Path, review_xlsx: Path) -> dict[str, int]:
    if not review_xlsx.is_file():
        raise FileNotFoundError(f"Review workbook not found: {review_xlsx}")
    docs = repo_root / "docs"
    inventory = read_csv(docs / "v2_candidate_inventory.csv")
    inventory_by_path = {row["source_image_path"]: row for row in inventory}
    if len(inventory_by_path) != len(inventory):
        raise ValueError("Inventory source-image paths are not unique")
    shadow_ids = {row["candidate_id"] for row in read_csv(docs / "v2_shadow_multilabel_manifest.csv")}
    review_rows = workbook_rows(review_xlsx)
    if not review_rows:
        raise ValueError("No review rows found in the workbook")

    review_ids = [row.get("A", "") for row in review_rows]
    duplicates = sorted(item for item, count in Counter(review_ids).items() if count > 1)
    if duplicates:
        raise ValueError(f"Duplicate review IDs: {', '.join(duplicates)}")
    decisions = [row.get("F", "").strip() for row in review_rows]
    invalid = sorted(set(decisions) - VALID_DECISIONS)
    if invalid:
        raise ValueError(f"Unsupported or incomplete review decisions: {', '.join(invalid)}")

    decision_records: list[dict[str, str]] = []
    no_shadow_records: list[dict[str, str]] = []
    for row in review_rows:
        source_path = row.get("D", "").strip()
        candidate = inventory_by_path.get(source_path)
        if candidate is None:
            raise ValueError(f"Reviewed path is absent from the V2 inventory: {source_path}")
        if candidate["source_id"] != "StreetSurfaceVis":
            raise ValueError(f"Reviewed path is not StreetSurfaceVis: {source_path}")
        if candidate["original_source_split"] != "train":
            raise ValueError(f"Reviewed path is not from the source training split: {source_path}")
        if candidate["proposed_multiclass_label"] != "normal_asphalt":
            raise ValueError(f"Reviewed path is not normal asphalt: {source_path}")
        if candidate["candidate_id"] in shadow_ids:
            raise ValueError(f"Reviewed no-shadow path already has a shadow overlay: {source_path}")
        verify_image(repo_root, source_path)
        decision = row["F"].strip()
        decision_records.append(
            {
                "review_id": row["A"].strip(),
                "candidate_id": candidate["candidate_id"],
                "source_dataset": candidate["source_id"],
                "source_split": candidate["original_source_split"],
                "source_record_id": candidate["source_record_id"],
                "source_image_path": source_path,
                "original_source_label": "Normal_asphalt",
                "human_decision": decision,
                "reviewer_notes": row.get("G", "").strip(),
                "training_status": (
                    "approved_no_shadow_candidate"
                    if decision == "no_shadow_clear"
                    else "excluded_from_no_shadow_candidate_set"
                ),
            }
        )
        if decision == "no_shadow_clear":
            no_shadow_records.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "primary_road_label": "normal_asphalt",
                    "verified_condition": "no_visible_road_shadow",
                    "review_id": row["A"].strip(),
                    "decision": decision,
                    "eligibility": "training_candidate",
                }
            )

    if not no_shadow_records:
        raise ValueError("The review contains no clear no-shadow examples")
    write_csv(docs / "v2_streetsurfacevis_no_shadow_review_decisions.csv", DECISION_FIELDS, decision_records)
    write_csv(docs / "v2_no_shadow_manifest.csv", MANIFEST_FIELDS, no_shadow_records)
    return {
        "reviewed_rows": len(decision_records),
        "approved_no_shadow": len(no_shadow_records),
        "shadow_present_excluded": sum(row["human_decision"] == "shadow_present" for row in decision_records),
        "unclear_excluded": sum(row["human_decision"] == "unclear_exclude" for row in decision_records),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--review-xlsx", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(finalize(args.repo_root.resolve(), args.review_xlsx.resolve()), indent=2))


if __name__ == "__main__":
    main()
