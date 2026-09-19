import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.audit_hf_manhole_covers import audit_dataset


def write_image(path: Path, color: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 6), color=color).save(path)


class HuggingFaceManholeAuditTests(unittest.TestCase):
    def test_only_source_train_manhole_is_a_candidate_and_duplicates_are_held(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data = root / "data/raw/v2/hf_manhole_covers"
            for split in ("train", "valid", "test"):
                for label in ("manhole", "void"):
                    write_image(data / split / split / label / f"{split}-{label}.jpg", "red")
            rows, report = audit_dataset(data, root)
        by_id = {row["source_record_id"]: row for row in rows}
        self.assertEqual(by_id["train::manhole::train-manhole.jpg"]["candidate_status"], "hold_exact_duplicate_before_split")
        self.assertEqual(by_id["train::void::train-void.jpg"]["candidate_status"], "reserved_not_v2_candidate")
        self.assertEqual(by_id["valid::manhole::valid-manhole.jpg"]["candidate_status"], "reserved_not_v2_candidate")
        self.assertEqual(report["images_readable"], 6)
        self.assertEqual(report["exact_duplicate_groups"], 1)


if __name__ == "__main__":
    unittest.main()
