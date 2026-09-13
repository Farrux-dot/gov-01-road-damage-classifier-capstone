import tempfile
import unittest
from pathlib import Path

from src.build_ceymo_candidate_manifest import build_manifest_records, summarize


def write_xml(path: Path, labels: list[str]) -> None:
    objects = "".join(
        "<object><name>"
        + label
        + "</name><bndbox><xmin>1</xmin><ymin>1</ymin>"
        "<xmax>10</xmax><ymax>10</ymax></bndbox></object>"
        for label in labels
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"<annotation>{objects}</annotation>", encoding="utf-8")


class BuildCeyMoCandidateManifestTests(unittest.TestCase):
    def test_duplicate_keeper_preserves_the_richer_annotation(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            images = root / "data/raw/v2/ceymo/train/extracted/train/images"
            annotations = root / "data/raw/v2/ceymo/train/extracted/train/bbox_annotations"
            images.mkdir(parents=True)
            (images / "copy_a.jpg").write_bytes(b"same-image")
            (images / "copy_b.jpg").write_bytes(b"same-image")
            (images / "unique.jpg").write_bytes(b"unique-image")
            write_xml(annotations / "copy_a.xml", ["SA"])
            write_xml(annotations / "copy_b.xml", ["SA", "RA"])
            write_xml(annotations / "unique.xml", ["PC"])

            records = build_manifest_records(root, images, annotations)

        by_id = {record["source_record_id"]: record for record in records}
        self.assertEqual(by_id["copy_a"]["candidate_status"], "exclude_exact_duplicate")
        self.assertEqual(by_id["copy_a"]["duplicate_role"], "redundant_copy")
        self.assertEqual(by_id["copy_b"]["candidate_status"], "pre_split_source_candidate")
        self.assertEqual(by_id["copy_b"]["duplicate_role"], "keeper")
        self.assertEqual(by_id["copy_a"]["exact_duplicate_group_id"], by_id["copy_b"]["exact_duplicate_group_id"])
        report = summarize(records)
        self.assertEqual(report["source_image_records"], 3)
        self.assertEqual(report["accepted_candidate_images"], 2)
        self.assertEqual(report["excluded_exact_duplicate_images"], 1)
        self.assertEqual(report["accepted_road_marking_objects"], 3)

    def test_equal_duplicate_annotations_use_stable_source_id_tiebreak(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            images = root / "images"
            annotations = root / "annotations"
            images.mkdir()
            (images / "first.jpg").write_bytes(b"same")
            (images / "second.jpg").write_bytes(b"same")
            write_xml(annotations / "first.xml", ["DM"])
            write_xml(annotations / "second.xml", ["DM"])

            records = build_manifest_records(root, images, annotations)

        by_id = {record["source_record_id"]: record for record in records}
        self.assertEqual(by_id["first"]["duplicate_role"], "keeper")
        self.assertEqual(by_id["second"]["candidate_status"], "exclude_exact_duplicate")

    def test_unknown_source_label_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            images = root / "images"
            annotations = root / "annotations"
            images.mkdir()
            (images / "bad.jpg").write_bytes(b"image")
            write_xml(annotations / "bad.xml", ["UNKNOWN"])

            with self.assertRaisesRegex(ValueError, "Unsupported CeyMo label"):
                build_manifest_records(root, images, annotations)


if __name__ == "__main__":
    unittest.main()
