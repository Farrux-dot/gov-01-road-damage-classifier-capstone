import csv
import json
import tempfile
import unittest
from pathlib import Path

from src.build_v2_candidate_inventory import build_inventory, mark_exact_duplicates, summarize


def write_svrdd_record(path: Path) -> None:
    record = {
        "file_name": "images/Example/svrdd.jpg",
        "image_id": "svrdd-1",
        "objects": {"v2_labels": ["crack", "pothole"]},
        "multi_labels": {
            "pothole_present": True,
            "crack_present": True,
            "manhole_cover_present": False,
            "repaired_road_present": False,
        },
        "multi_class_label": "pothole",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")


class BuildV2CandidateInventoryTests(unittest.TestCase):
    def test_inventory_uses_only_eligible_sources_and_keeps_v1_evaluation_reserved(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            annotations = root / "data/processed/v2/svrdd/annotations"
            extracted = root / "data/raw/v2/svrdd/extracted"
            for split in ("train", "validation", "test"):
                write_svrdd_record(annotations / f"{split}.v2.jsonl")
                image = extracted / split / "images/Example/svrdd.jpg"
                image.parent.mkdir(parents=True, exist_ok=True)
                image.write_bytes(f"svrdd-{split}".encode())

            clean_split = root / "data/processed/clean_split"
            for split in ("train", "validation", "test"):
                image = clean_split / split / "Pothole" / f"v1-{split}.jpg"
                image.parent.mkdir(parents=True, exist_ok=True)
                image.write_bytes(f"v1-{split}".encode())

            pave_image = root / "data/raw/v2/pavebench/approved.jpg"
            pave_image.parent.mkdir(parents=True, exist_ok=True)
            pave_image.write_bytes(b"approved-pavebench")
            excluded_image = root / "data/raw/v2/pavebench/excluded.jpg"
            excluded_image.write_bytes(b"excluded-pavebench")
            review_manifest = root / "docs/v2_pavebench_detection_review_manifest.csv"
            review_manifest.parent.mkdir(parents=True, exist_ok=True)
            with review_manifest.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=("sample_id", "source_class", "source_file", "record_action"),
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "sample_id": "approved-1",
                        "source_class": "alligator",
                        "source_file": "data/raw/v2/pavebench/approved.jpg",
                        "record_action": "candidate_keep_reviewed_sample",
                    }
                )
                writer.writerow(
                    {
                        "sample_id": "excluded-1",
                        "source_class": "crack",
                        "source_file": "data/raw/v2/pavebench/excluded.jpg",
                        "record_action": "exclude_unclear",
                    }
                )

            records = build_inventory(root, annotations, extracted, clean_split, review_manifest)

        self.assertEqual(len(records), 3)
        paths = {record["source_image_path"] for record in records}
        self.assertIn("data/raw/v2/svrdd/extracted/train/images/Example/svrdd.jpg", paths)
        self.assertNotIn("data/raw/v2/svrdd/extracted/validation/images/Example/svrdd.jpg", paths)
        self.assertNotIn("data/raw/v2/svrdd/extracted/test/images/Example/svrdd.jpg", paths)
        self.assertIn("data/processed/clean_split/train/Pothole/v1-train.jpg", paths)
        self.assertNotIn("data/processed/clean_split/validation/Pothole/v1-validation.jpg", paths)
        self.assertNotIn("data/processed/clean_split/test/Pothole/v1-test.jpg", paths)
        self.assertIn("data/raw/v2/pavebench/approved.jpg", paths)
        self.assertNotIn("data/raw/v2/pavebench/excluded.jpg", paths)

    def test_exact_duplicates_are_flagged_not_silently_removed(self):
        records = [
            {"candidate_id": "one", "sha256": "same", "candidate_status": "candidate", "exact_duplicate_group_id": ""},
            {"candidate_id": "two", "sha256": "same", "candidate_status": "candidate", "exact_duplicate_group_id": ""},
            {"candidate_id": "three", "sha256": "different", "candidate_status": "candidate", "exact_duplicate_group_id": ""},
        ]
        mark_exact_duplicates(records)
        self.assertEqual(records[0]["exact_duplicate_group_id"], "exact_dup_0001")
        self.assertEqual(records[1]["exact_duplicate_group_id"], "exact_dup_0001")
        self.assertEqual(records[0]["candidate_status"], "hold_exact_duplicate_before_split")
        self.assertEqual(records[2]["exact_duplicate_group_id"], "")

    def test_summary_is_inventory_evidence_not_model_performance(self):
        records = [
            {
                "source_id": "source",
                "proposed_multiclass_label": "crack",
                "task_eligibility": "multi_class;multi_label;object_detection",
                "proposed_multilabels": "crack",
                "object_label_counts": "crack:2",
                "exact_duplicate_group_id": "",
                "source_image_path": "data/raw/example.jpg",
            }
        ]
        report = summarize(records)
        self.assertEqual(report["candidate_image_records"], 1)
        self.assertEqual(report["counts_by_positive_multilabel"], {"crack": 1})
        self.assertEqual(report["object_counts_by_label"], {"crack": 2})
        self.assertEqual(report["svrdd_candidate_source_splits"], ["train"])
        self.assertEqual(report["svrdd_reserved_source_splits"], ["validation", "test"])
        self.assertEqual(report["inventory_status"], "pre_split_candidates_only_not_ready_for_training")
        self.assertNotIn("accuracy", report)


if __name__ == "__main__":
    unittest.main()
