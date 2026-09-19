import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from src.build_v2_candidate_inventory import (
    build_inventory,
    build_kaggle_speed_bump_candidates,
    mark_exact_duplicates,
    summarize,
)


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


def write_streetsurfacevis_manifest(root: Path) -> Path:
    manifest = root / "docs/v2_streetsurfacevis_candidate_manifest.csv"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = (
        "image_id",
        "candidate_label",
        "review_sample_id",
        "human_review_decision",
        "reviewer_notes",
        "official_train",
        "resolution_decision",
        "sha256",
        "relative_image_path",
    )
    examples = (
        ("normal-1", "Normal_asphalt", "", "", "True", "eligible"),
        ("unpaved-keep", "Unpaved_road", "SSV-001", "Keep", "True", "eligible"),
        ("unpaved-unclear", "Unpaved_road", "SSV-055", "Unclear", "True", "eligible"),
        ("protected", "Normal_asphalt", "", "", "False", "eligible"),
        ("too-small", "Normal_asphalt", "", "", "True", "hold_below_224"),
    )
    with manifest.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for image_id, label, sample_id, decision, official_train, resolution_decision in examples:
            relative_path = f"data/raw/v2/streetsurfacevis/s_1024/{image_id}.jpg"
            image_path = root / relative_path
            image_path.parent.mkdir(parents=True, exist_ok=True)
            image_bytes = f"streetsurfacevis-{image_id}".encode()
            image_path.write_bytes(image_bytes)
            writer.writerow(
                {
                    "image_id": image_id,
                    "candidate_label": label,
                    "review_sample_id": sample_id,
                    "human_review_decision": decision,
                    "reviewer_notes": "",
                    "official_train": official_train,
                    "resolution_decision": resolution_decision,
                    "sha256": hashlib.sha256(image_bytes).hexdigest(),
                    "relative_image_path": relative_path,
                }
            )
    return manifest


def write_ceymo_manifest(root: Path) -> Path:
    manifest = root / "docs/v2_ceymo_candidate_manifest.csv"
    accepted_image = root / "data/raw/v2/ceymo/train/extracted/train/images/marking.jpg"
    accepted_xml = root / "data/raw/v2/ceymo/train/extracted/train/bbox_annotations/marking.xml"
    accepted_image.parent.mkdir(parents=True, exist_ok=True)
    accepted_xml.parent.mkdir(parents=True, exist_ok=True)
    accepted_image.write_bytes(b"ceymo-marking")
    accepted_xml.write_text("<annotation></annotation>", encoding="utf-8")
    fieldnames = (
        "source_record_id",
        "source_image_path",
        "source_annotation_path",
        "source_subtype_counts",
        "mapped_object_count",
        "sha256",
        "exact_duplicate_group_id",
        "candidate_status",
    )
    with manifest.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "source_record_id": "marking",
                "source_image_path": "data/raw/v2/ceymo/train/extracted/train/images/marking.jpg",
                "source_annotation_path": "data/raw/v2/ceymo/train/extracted/train/bbox_annotations/marking.xml",
                "source_subtype_counts": "SA:2",
                "mapped_object_count": "2",
                "sha256": hashlib.sha256(b"ceymo-marking").hexdigest(),
                "exact_duplicate_group_id": "ceymo_exact_dup_0001",
                "candidate_status": "pre_split_source_candidate",
            }
        )
        writer.writerow(
            {
                "source_record_id": "excluded-copy",
                "source_image_path": "data/raw/v2/ceymo/train/extracted/train/images/excluded.jpg",
                "source_annotation_path": "data/raw/v2/ceymo/train/extracted/train/bbox_annotations/excluded.xml",
                "source_subtype_counts": "SA:1",
                "mapped_object_count": "1",
                "sha256": "excluded",
                "exact_duplicate_group_id": "ceymo_exact_dup_0001",
                "candidate_status": "exclude_exact_duplicate",
            }
        )
    return manifest


def write_github_pothole_manifest(root: Path) -> Path:
    manifest = root / "docs/v2_github_pothole_candidate_manifest.csv"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    image = root / "data/raw/v2/pothole_github/Pothole Dataset/pothole.jpg"
    label = root / "data/raw/v2/pothole_github/Pothole Dataset/pothole.txt"
    image.parent.mkdir(parents=True, exist_ok=True)
    image_bytes = b"github-pothole"
    image.write_bytes(image_bytes)
    label.write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
    fieldnames = (
        "source_id", "relative_image_path", "relative_label_path", "sha256",
        "valid_pothole_boxes", "decision",
    )
    with manifest.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "source_id": "github_pothole::keep",
                "relative_image_path": "data/raw/v2/pothole_github/Pothole Dataset/pothole.jpg",
                "relative_label_path": "data/raw/v2/pothole_github/Pothole Dataset/pothole.txt",
                "sha256": hashlib.sha256(image_bytes).hexdigest(),
                "valid_pothole_boxes": "1",
                "decision": "keep",
            }
        )
        writer.writerow(
            {
                "source_id": "github_pothole::excluded",
                "relative_image_path": "data/raw/v2/pothole_github/Pothole Dataset/excluded.jpg",
                "relative_label_path": "data/raw/v2/pothole_github/Pothole Dataset/excluded.txt",
                "sha256": "excluded",
                "valid_pothole_boxes": "1",
                "decision": "exclude",
            }
        )
    return manifest


def write_hf_manhole_manifest(root: Path) -> Path:
    manifest = root / "docs/v2_hf_manhole_covers_audit_manifest.csv"
    image = root / "data/raw/v2/hf_manhole_covers/train/train/manhole/manhole.jpg"
    image.parent.mkdir(parents=True, exist_ok=True)
    image_bytes = b"hf-manhole"
    image.write_bytes(image_bytes)
    fields = ("source_record_id", "relative_image_path", "sha256", "exact_duplicate_group_id", "candidate_status")
    with manifest.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerow({
            "source_record_id": "train::manhole::manhole.jpg",
            "relative_image_path": "data/raw/v2/hf_manhole_covers/train/train/manhole/manhole.jpg",
            "sha256": hashlib.sha256(image_bytes).hexdigest(),
            "exact_duplicate_group_id": "",
            "candidate_status": "source_train_manhole_candidate",
        })
        writer.writerow({
            "source_record_id": "valid::manhole::reserved.jpg",
            "relative_image_path": "data/raw/v2/hf_manhole_covers/valid/valid/manhole/reserved.jpg",
            "sha256": "reserved",
            "exact_duplicate_group_id": "",
            "candidate_status": "reserved_not_v2_candidate",
        })
    return manifest


def write_kaggle_speed_bump_manifest(root: Path) -> Path:
    manifest = root / "docs/v2_kaggle_speed_bump_audit_manifest.csv"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    image = root / "data/raw/v2/kaggle_speed_bump/Dataset/Data/bump/bump.jpg"
    image.parent.mkdir(parents=True, exist_ok=True)
    image_bytes = b"kaggle-speed-bump"
    image.write_bytes(image_bytes)
    fields = ("source_record_id", "relative_image_path", "sha256", "decision")
    with manifest.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerow({
            "source_record_id": "bump::bump.jpg",
            "relative_image_path": "data/raw/v2/kaggle_speed_bump/Dataset/Data/bump/bump.jpg",
            "sha256": hashlib.sha256(image_bytes).hexdigest(),
            "decision": "keep_speed_bump_candidate",
        })
        writer.writerow({
            "source_record_id": "bump::MVI_demo 001.jpg",
            "relative_image_path": "data/raw/v2/kaggle_speed_bump/Dataset/Data/bump/MVI_demo 001.jpg",
            "sha256": "sequence",
            "decision": "exclude_sequence_risk",
        })
    return manifest


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

            github_pothole_manifest = write_github_pothole_manifest(root)
            streetsurfacevis_manifest = write_streetsurfacevis_manifest(root)
            ceymo_manifest = write_ceymo_manifest(root)
            hf_manhole_manifest = write_hf_manhole_manifest(root)
            records = build_inventory(
                root,
                annotations,
                extracted,
                clean_split,
                github_pothole_manifest,
                streetsurfacevis_manifest,
                ceymo_manifest,
                hf_manhole_manifest,
            )

        self.assertEqual(len(records), 7)
        paths = {record["source_image_path"] for record in records}
        self.assertIn("data/raw/v2/svrdd/extracted/train/images/Example/svrdd.jpg", paths)
        self.assertNotIn("data/raw/v2/svrdd/extracted/validation/images/Example/svrdd.jpg", paths)
        self.assertNotIn("data/raw/v2/svrdd/extracted/test/images/Example/svrdd.jpg", paths)
        self.assertIn("data/processed/clean_split/train/Pothole/v1-train.jpg", paths)
        self.assertNotIn("data/processed/clean_split/validation/Pothole/v1-validation.jpg", paths)
        self.assertNotIn("data/processed/clean_split/test/Pothole/v1-test.jpg", paths)
        self.assertIn("data/raw/v2/pothole_github/Pothole Dataset/pothole.jpg", paths)
        self.assertNotIn("data/raw/v2/pothole_github/Pothole Dataset/excluded.jpg", paths)
        self.assertIn("data/raw/v2/streetsurfacevis/s_1024/normal-1.jpg", paths)
        self.assertIn("data/raw/v2/streetsurfacevis/s_1024/unpaved-keep.jpg", paths)
        self.assertNotIn("data/raw/v2/streetsurfacevis/s_1024/unpaved-unclear.jpg", paths)
        self.assertNotIn("data/raw/v2/streetsurfacevis/s_1024/protected.jpg", paths)
        self.assertNotIn("data/raw/v2/streetsurfacevis/s_1024/too-small.jpg", paths)
        self.assertIn("data/raw/v2/ceymo/train/extracted/train/images/marking.jpg", paths)
        self.assertNotIn("data/raw/v2/ceymo/train/extracted/train/images/excluded.jpg", paths)
        self.assertIn("data/raw/v2/hf_manhole_covers/train/train/manhole/manhole.jpg", paths)
        street_records = [record for record in records if record["source_id"] == "StreetSurfaceVis"]
        self.assertEqual({record["task_eligibility"] for record in street_records}, {"multi_class"})
        self.assertEqual({record["proposed_multilabels"] for record in street_records}, {""})
        ceymo_records = [record for record in records if record["source_id"] == "CeyMo"]
        self.assertEqual(len(ceymo_records), 1)
        self.assertEqual(ceymo_records[0]["task_eligibility"], "multi_label;object_detection")
        self.assertEqual(ceymo_records[0]["proposed_multiclass_label"], "")
        self.assertEqual(ceymo_records[0]["proposed_multilabels"], "road_marking")
        self.assertEqual(ceymo_records[0]["object_label_counts"], "road_marking:2")
        github_records = [record for record in records if record["source_id"] == "jaygala24_pothole_detection"]
        self.assertEqual(len(github_records), 1)
        self.assertEqual(github_records[0]["object_label_counts"], "pothole:1")
        hf_manhole_records = [record for record in records if record["source_id"] == "delima87_manhole_covers_dataset"]
        self.assertEqual(len(hf_manhole_records), 1)
        self.assertEqual(hf_manhole_records[0]["proposed_multiclass_label"], "manhole_cover")
        self.assertEqual(hf_manhole_records[0]["boxes_available"], "no")

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

    def test_speed_bump_inventory_keeps_only_audited_non_sequence_candidates(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            records = build_kaggle_speed_bump_candidates(root, write_kaggle_speed_bump_manifest(root))

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["source_record_id"], "bump::bump.jpg")
        self.assertEqual(records[0]["proposed_multiclass_label"], "speed_bump")
        self.assertEqual(records[0]["proposed_multilabels"], "speed_bump")
        self.assertEqual(records[0]["boxes_available"], "no")

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
