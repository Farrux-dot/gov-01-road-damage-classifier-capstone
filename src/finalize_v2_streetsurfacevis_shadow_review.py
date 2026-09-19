"""Import the completed human review of StreetSurfaceVis shadow candidates.

This script records decisions only. It does not copy images, create a final
split, train a model, or claim that the shadow tag is ground truth outside the
human-reviewed images.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

try:  # Supports both `python src/file.py` and `python -m src.file`.
    from src.finalize_v2_no_shadow_review import verify_image, workbook_rows
except ModuleNotFoundError:  # pragma: no cover - exercised by the CLI command path.
    from finalize_v2_no_shadow_review import verify_image, workbook_rows


VALID_DECISIONS = {"keep_shadow", "exclude_no_shadow"}
DECISION_FIELDS = (
    "review_id",
    "candidate_id",
    "source_dataset",
    "source_split",
    "source_record_id",
    "source_image_path",
    "primary_road_label",
    "human_decision",
    "reviewer_notes",
    "training_status",
)
OVERLAY_FIELDS = (
    "candidate_id",
    "primary_road_label",
    "added_multilabel",
    "review_manifest_id",
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


def shadow_workbook_rows(workbook_path: Path) -> list[dict[str, str]]:
    """Read rows whose review IDs start with SHC- from the review workbook."""
    return workbook_rows(workbook_path, review_id_prefix="SHC-")


def finalize(repo_root: Path, review_xlsx: Path) -> dict[str, int]:
    if not review_xlsx.is_file():
        raise FileNotFoundError(f"Review workbook not found: {review_xlsx}")

    docs = repo_root / "docs"
    candidates = read_csv(docs / "v2_streetsurfacevis_shadow_heuristic_candidates.csv")
    candidate_by_review_id = {row["review_id"]: row for row in candidates}
    if len(candidate_by_review_id) != len(candidates):
        raise ValueError("Shadow candidate review IDs are not unique")

    inventory = read_csv(docs / "v2_candidate_inventory.csv")
    inventory_by_path = {row["source_image_path"]: row for row in inventory}
    existing_overlays = read_csv(docs / "v2_shadow_multilabel_manifest.csv")
    existing_ids = {row["candidate_id"] for row in existing_overlays}
    no_shadow_ids = {row["candidate_id"] for row in read_csv(docs / "v2_no_shadow_manifest.csv")}

    review_rows = shadow_workbook_rows(review_xlsx)
    if not review_rows:
        raise ValueError("No SHC review rows found in the workbook")
    review_ids = [row.get("A", "").strip() for row in review_rows]
    duplicate_ids = sorted(item for item, count in Counter(review_ids).items() if count > 1)
    if duplicate_ids:
        raise ValueError(f"Duplicate review IDs: {', '.join(duplicate_ids)}")
    if set(review_ids) != set(candidate_by_review_id):
        raise ValueError("Workbook review IDs do not exactly match the prepared candidate list")

    # The workbook intentionally exposes only a compact review view:
    # A=review ID, C=road label, D=heuristic score, E=decision, F=notes.
    # Traceable source paths remain in the prepared candidate CSV, not Excel.
    decisions = [row.get("E", "").strip() for row in review_rows]
    invalid = sorted(set(decisions) - VALID_DECISIONS)
    if invalid:
        raise ValueError(f"Unsupported or incomplete review decisions: {', '.join(invalid)}")

    decision_records: list[dict[str, str]] = []
    new_overlays: list[dict[str, str]] = []
    for row in review_rows:
        review_id = row["A"].strip()
        prepared = candidate_by_review_id[review_id]
        source_path = prepared["source_image_path"]
        candidate = inventory_by_path.get(source_path)
        if candidate is None:
            raise ValueError(f"Reviewed path is absent from the V2 inventory: {source_path}")
        if candidate["candidate_id"] != prepared["candidate_id"]:
            raise ValueError(f"Candidate ID mismatch for {review_id}")
        if candidate["source_id"] != "StreetSurfaceVis" or candidate["original_source_split"] != "train":
            raise ValueError(f"Reviewed record is not eligible StreetSurfaceVis training data: {review_id}")
        if candidate["proposed_multiclass_label"] not in {"normal_asphalt", "unpaved_road"}:
            raise ValueError(f"Reviewed record has an unsupported road label: {review_id}")
        if candidate["candidate_id"] in existing_ids:
            raise ValueError(f"Reviewed record already has a shadow overlay: {review_id}")
        if candidate["candidate_id"] in no_shadow_ids:
            raise ValueError(f"Reviewed record is already confirmed no-shadow: {review_id}")
        verify_image(repo_root, source_path)

        decision = row["E"].strip()
        decision_records.append(
            {
                "review_id": review_id,
                "candidate_id": candidate["candidate_id"],
                "source_dataset": candidate["source_id"],
                "source_split": candidate["original_source_split"],
                "source_record_id": candidate["source_record_id"],
                "source_image_path": source_path,
                "primary_road_label": candidate["proposed_multiclass_label"],
                "human_decision": decision,
                "reviewer_notes": row.get("F", "").strip(),
                "training_status": "approved_shadow_candidate" if decision == "keep_shadow" else "excluded_from_shadow_candidate_set",
            }
        )
        if decision == "keep_shadow":
            new_overlays.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "primary_road_label": candidate["proposed_multiclass_label"],
                    "added_multilabel": "shadow",
                    "review_manifest_id": review_id,
                    "decision": "approved",
                    "eligibility": "training_candidate",
                }
            )

    if not new_overlays:
        raise ValueError("The review contains no approved shadow examples")
    write_csv(docs / "v2_streetsurfacevis_shadow_heuristic_review_decisions.csv", DECISION_FIELDS, decision_records)
    write_csv(docs / "v2_shadow_multilabel_manifest.csv", OVERLAY_FIELDS, existing_overlays + new_overlays)
    return {
        "reviewed_rows": len(decision_records),
        "approved_shadow": len(new_overlays),
        "excluded_no_shadow": len(decision_records) - len(new_overlays),
        "total_shadow_overlays": len(existing_overlays) + len(new_overlays),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--review-xlsx", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(finalize(args.repo_root.resolve(), args.review_xlsx.resolve()), indent=2))


if __name__ == "__main__":
    main()
