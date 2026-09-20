"""Focused checks for the V2 split-manifest generator."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from build_v2_split_manifest import build_manifest, validate_manifest  # noqa: E402


def record(candidate_id: str, label: str, source: str, record_id: str) -> dict[str, str]:
    return {
        "candidate_id": candidate_id,
        "source_id": source,
        "source_record_id": record_id,
        "source_image_path": f"data/raw/{candidate_id}.jpg",
        "sha256": candidate_id,
        "task_eligibility": "multi_class",
        "proposed_multiclass_label": label,
        "original_source_split": "train",
    }


class V2SplitManifestTests(unittest.TestCase):
    def test_is_deterministic_and_assigns_every_eligible_candidate_once(self) -> None:
        rows = [record(f"p{index}", "pothole", "source_a", str(index)) for index in range(10)]
        first = build_manifest(rows, seed=42)
        second = build_manifest(rows, seed=42)
        self.assertEqual(first, second)
        self.assertEqual({item["candidate_id"] for item in first}, {item["candidate_id"] for item in rows})
        self.assertEqual({item["split"] for item in first}, {"train", "validation", "protected_test"})
        validate_manifest(first)

    def test_keeps_related_records_in_one_split_group(self) -> None:
        rows = [
            record("first_crop", "crack", "source_a", "original_1"),
            record("second_crop", "crack", "source_a", "original_1"),
            *[record(f"other_{index}", "crack", "source_a", f"original_{index + 2}") for index in range(8)],
        ]
        manifest = build_manifest(rows, seed=42)
        related_splits = {item["split"] for item in manifest if item["split_group_id"] == "source_a::original_1"}
        self.assertEqual(len(related_splits), 1)
        validate_manifest(manifest)

    def test_tiny_source_label_stratum_stays_in_training(self) -> None:
        rows = [record("only_one", "manhole_cover", "rare_source", "one")]
        manifest = build_manifest(rows, seed=42)
        self.assertEqual(manifest[0]["split"], "train")
        validate_manifest(manifest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
