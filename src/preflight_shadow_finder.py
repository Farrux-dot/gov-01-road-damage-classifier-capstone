"""Validate the approved inputs for the V2 road-shadow finder experiment.

This is a data-preparation check, not a model-training script.  It verifies
that the approved SRD, ISTD, and StreetSurfaceVis records are traceable and
that the StreetSurfaceVis overlay refers only to existing training candidates.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from PIL import Image


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def resolve_inside_repo(repo_root: Path, relative_path: str) -> Path:
    """Resolve a recorded relative path and reject paths outside the project."""
    candidate = (repo_root / relative_path).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError as error:
        raise ValueError(f"Path escapes the repository: {relative_path}") from error
    return candidate


def verify_image(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Missing file: {path}")
    with Image.open(path) as image:
        image.verify()


def build_preflight(repo_root: Path) -> dict[str, object]:
    docs = repo_root / "docs"
    inventory = read_csv(docs / "v2_candidate_inventory.csv")
    inventory_by_id = {row["candidate_id"]: row for row in inventory}

    srd_rows = read_csv(docs / "v2_srd_shadow_approved_manifest.csv")
    istd_rows = read_csv(docs / "v2_istd_shadow_approved_manifest.csv")
    overlay_rows = read_csv(docs / "v2_shadow_multilabel_manifest.csv")
    no_shadow_rows = read_csv(docs / "v2_no_shadow_manifest.csv")

    srd_kept = [row for row in srd_rows if row["human_decision"].lower() == "keep"]
    istd_kept = [row for row in istd_rows if row["review_decision"].lower() == "keep"]

    for row in srd_kept:
        verify_image(resolve_inside_repo(repo_root, row["local_image"]))
        verify_image(resolve_inside_repo(repo_root, row["local_mask"]))

    for row in istd_kept:
        verify_image(resolve_inside_repo(repo_root, row["image_path"]))
        verify_image(resolve_inside_repo(repo_root, row["shadow_mask_path"]))

    for row in overlay_rows:
        candidate = inventory_by_id.get(row["candidate_id"])
        if candidate is None:
            raise ValueError(f"Overlay candidate is missing from inventory: {row['candidate_id']}")
        if candidate["original_source_split"] != "train":
            raise ValueError(f"Overlay candidate is not from the source training split: {row['candidate_id']}")
        if candidate["proposed_multiclass_label"] != "normal_asphalt":
            raise ValueError(f"Overlay candidate is not normal asphalt: {row['candidate_id']}")
        if row["added_multilabel"] != "shadow" or row["decision"] != "approved":
            raise ValueError(f"Invalid shadow overlay decision: {row['candidate_id']}")
        verify_image(resolve_inside_repo(repo_root, candidate["source_image_path"]))

    shadow_ids = {row["candidate_id"] for row in overlay_rows}
    no_shadow_ids = {row["candidate_id"] for row in no_shadow_rows}
    overlap = sorted(shadow_ids & no_shadow_ids)
    if overlap:
        raise ValueError(f"A candidate cannot be both shadow and no-shadow: {overlap[0]}")
    for row in no_shadow_rows:
        candidate = inventory_by_id.get(row["candidate_id"])
        if candidate is None:
            raise ValueError(f"No-shadow candidate is missing from inventory: {row['candidate_id']}")
        if candidate["original_source_split"] != "train":
            raise ValueError(f"No-shadow candidate is not from the source training split: {row['candidate_id']}")
        if candidate["proposed_multiclass_label"] != "normal_asphalt":
            raise ValueError(f"No-shadow candidate is not normal asphalt: {row['candidate_id']}")
        if row["verified_condition"] != "no_visible_road_shadow" or row["decision"] != "no_shadow_clear":
            raise ValueError(f"Invalid no-shadow review decision: {row['candidate_id']}")
        verify_image(resolve_inside_repo(repo_root, candidate["source_image_path"]))

    return {
        "srd_approved_images": len(srd_kept),
        "istd_approved_images": len(istd_kept),
        "streetsurfacevis_approved_training_images": len(overlay_rows),
        "streetsurfacevis_approved_no_shadow_images": len(no_shadow_rows),
        "total_approved_shadow_examples": len(srd_kept) + len(istd_kept) + len(overlay_rows),
        "shadow_and_no_shadow_sets_do_not_overlap": True,
        "srd_and_istd_have_masks": True,
        "streetsurfacevis_overlay_is_training_only": True,
        "training_status": "blocked",
        "training_blocker": (
            "No final V2 split exists yet. SRD provenance and ISTD "
            "non-commercial conditions must be confirmed before any training use."
        ),
        "safe_next_use": "Use only for a documented candidate-mining experiment after the blockers are resolved; do not auto-label results.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Project root containing docs/ and data/ (default: repository root).",
    )
    args = parser.parse_args()
    print(json.dumps(build_preflight(args.repo_root.resolve()), indent=2))


if __name__ == "__main__":
    main()
