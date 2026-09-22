from __future__ import annotations

import csv
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from materialize_v2_multiclass_final_split import (  # noqa: E402
    destination_for,
    materialize,
)


class MaterializationTests(unittest.TestCase):
    def test_materialize_preserves_source_bytes_and_uses_class_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "data" / "raw" / "example.jpg"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"example-image-bytes")
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            row = {
                "candidate_id": "example::1",
                "source_image_path": "data/raw/example.jpg",
                "sha256": source_hash,
                "proposed_multiclass_label": "pothole",
                "split_group_id": "example-group",
                "split": "train",
            }
            output_root = root / "data" / "processed" / "v2" / "multiclass_final"
            output = materialize([row], root, output_root, dry_run=False, resume=False)

            destination = destination_for(row, output_root)
            self.assertTrue(destination.is_file())
            self.assertEqual(destination.read_bytes(), source.read_bytes())
            self.assertEqual(output[0]["verification_status"], "copied_hash_matches_source")

            resumed = materialize([row], root, output_root, dry_run=False, resume=True)
            self.assertEqual(resumed[0]["verification_status"], "existing_hash_matches_source")


if __name__ == "__main__":
    unittest.main()
