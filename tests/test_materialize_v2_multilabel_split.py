from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.build_v2_multilabel_coverage_manifest import ACTIVE_CONDITIONS
from src.materialize_v2_multilabel_split import materialize, prepare_materialization


def _manifest(record_id: str, image_path: Path) -> dict[str, str]:
    row = {"record_id": record_id, "source_dataset": "source", "image_reference": str(image_path)}
    for condition in ACTIVE_CONDITIONS:
        row[f"{condition}_known"] = "1"
        row[f"{condition}_present"] = "0"
    return row


class MultiLabelMaterializationTests(unittest.TestCase):
    def test_copies_source_bytes_and_writes_split_labels(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.jpg"
            source_bytes = b"test image bytes"
            source.write_bytes(source_bytes)
            digest = __import__("hashlib").sha256(source_bytes).hexdigest()
            prepared = prepare_materialization(
                [_manifest("one", source)],
                [{"record_id": "one", "source_dataset": "source", "planned_split": "train"}],
                [{"record_id": "one", "image_reference": str(source), "readable": "yes", "sha256": digest}],
            )
            target = root / "processed"
            summary = materialize(prepared, target)

            copied = next((target / "train" / "images").iterdir())
            self.assertEqual(copied.read_bytes(), source_bytes)
            self.assertEqual(source.read_bytes(), source_bytes)
            self.assertEqual(summary["splits"]["train"], 1)
            self.assertTrue((target / "train" / "labels.csv").is_file())

    def test_refuses_to_overwrite_existing_target(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = Path(temporary_directory) / "processed"
            target.mkdir()
            with self.assertRaises(FileExistsError):
                materialize([], target)


if __name__ == "__main__":
    unittest.main()
