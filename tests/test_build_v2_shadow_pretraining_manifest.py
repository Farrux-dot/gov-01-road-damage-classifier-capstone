"""Tests for selecting safe SRD/ISTD shadow-pattern staging records."""

from __future__ import annotations

import unittest

from src.build_v2_shadow_pretraining_manifest import select_training_candidates


def row(audit_id: str, source_split: str, image_hash: str) -> dict[str, str]:
    return {
        "audit_id": audit_id,
        "source_key": "srd",
        "source_dataset": "SRD",
        "source_split": source_split,
        "source_image_path": f"data/{audit_id}.jpg",
        "width": "640",
        "height": "480",
        "image_sha256": image_hash,
        "mask_sha256": "mask",
        "shadow_mask_coverage": "0.25",
        "audit_status": "structurally_valid_not_integrated",
    }


class ShadowPretrainingManifestTests(unittest.TestCase):
    def test_keeps_training_only_and_one_exact_duplicate(self) -> None:
        selected, counts = select_training_candidates(
            [row("SRD_FULL_00002", "train", "same"), row("SRD_FULL_00001", "train", "same"), row("SRD_FULL_00003", "test", "other")]
        )
        self.assertEqual([item["audit_id"] for item in selected], ["SRD_FULL_00001"])
        self.assertEqual(counts["exact_duplicate_records_excluded"], 1)

    def test_rejects_non_structurally_valid_records(self) -> None:
        invalid = row("SRD_FULL_00001", "train", "hash")
        invalid["audit_status"] = "failed"
        selected, counts = select_training_candidates([invalid])
        self.assertEqual(selected, [])
        self.assertEqual(counts["source_training_records"], 0)


if __name__ == "__main__":
    unittest.main()
