import csv
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from src.build_v2_multilabel_coverage_manifest import build_manifest


class CoverageManifestTests(unittest.TestCase):
    def test_manifest_preserves_unknown_labels_instead_of_making_them_absent(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            images_root = root / "svrdd_images"
            image_path = images_root / "images" / "region" / "one.jpg"
            image_path.parent.mkdir(parents=True)
            image_path.write_bytes(b"placeholder")
            metadata_path = root / "train.metadata.jsonl"
            metadata_path.write_text(
                json.dumps(
                    {
                        "file_name": "images/region/one.jpg",
                        "image_id": "one",
                        "objects": {"category_names": ["pothole", "longitudinal crack"]},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            rtk_images = root / "rtk_images.zip"
            rtk_annotations = root / "rtk_annotations.zip"
            with zipfile.ZipFile(rtk_images, "w") as archive:
                for number in range(701):
                    archive.writestr(f"{number:09d}.png", b"placeholder")
            with zipfile.ZipFile(rtk_annotations, "w") as archive:
                for number in range(701):
                    labels = ["roadMarking"] if number == 0 else ["roadAsphalt"]
                    archive.writestr(f"{number:09d}.json", json.dumps({"shapes": [{"label": label} for label in labels]}))
            output_csv = root / "coverage.csv"
            summary_json = root / "summary.json"
            result = build_manifest(
                svrdd_metadata=metadata_path,
                svrdd_images_root=images_root,
                rtk_images_archive=rtk_images,
                rtk_annotations_archive=rtk_annotations,
                output_csv=output_csv,
                summary_json=summary_json,
            )
            self.assertEqual(result["total_records"], 702)
            with output_csv.open(newline="", encoding="utf-8") as source:
                rows = list(csv.DictReader(source))
            svrdd_row = rows[0]
            rtk_row = rows[1]
            self.assertEqual(svrdd_row["pothole_known"], "1")
            self.assertEqual(svrdd_row["pothole_present"], "1")
            self.assertEqual(svrdd_row["road_marking_known"], "0")
            self.assertEqual(svrdd_row["road_marking_present"], "")
            self.assertEqual(rtk_row["road_marking_known"], "1")
            self.assertEqual(rtk_row["road_marking_present"], "1")
            self.assertEqual(rtk_row["manhole_cover_known"], "0")
            self.assertEqual(rtk_row["manhole_cover_present"], "")

    def test_speed_bump_sources_keep_other_conditions_unknown_and_reject_known_conflicts(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            images_root = root / "svrdd_images"
            source_image = images_root / "images" / "region" / "one.jpg"
            source_image.parent.mkdir(parents=True)
            source_image.write_bytes(b"svrdd")
            metadata_path = root / "train.metadata.jsonl"
            metadata_path.write_text(json.dumps({"file_name": "images/region/one.jpg", "image_id": "one", "objects": {"category_names": ["pothole"]}}) + "\n", encoding="utf-8")
            rtk_images = root / "rtk_images.zip"
            rtk_annotations = root / "rtk_annotations.zip"
            with zipfile.ZipFile(rtk_images, "w") as image_archive, zipfile.ZipFile(rtk_annotations, "w") as annotation_archive:
                for number in range(701):
                    image_archive.writestr(f"{number:09d}.png", b"placeholder")
                    annotation_archive.writestr(f"{number:09d}.json", json.dumps({"shapes": [{"label": "roadAsphalt"}]}))
            kaggle_image = root / "data" / "raw" / "kaggle" / "speed.jpg"
            kaggle_image.parent.mkdir(parents=True)
            kaggle_image.write_bytes(b"kaggle-speed-bump")
            kaggle_hash = __import__("hashlib").sha256(kaggle_image.read_bytes()).hexdigest()
            kaggle_audit = root / "kaggle.csv"
            kaggle_audit.write_text(
                "source_record_id,relative_image_path,sha256,decision\n"
                f"train::bump::speed.jpg,data/raw/kaggle/speed.jpg,{kaggle_hash},keep_train_speed_bump_candidate\n",
                encoding="utf-8",
            )
            mendeley_root = root / "mendeley"
            mendeley_root.mkdir()
            (mendeley_root / "safe.jpg").write_bytes(b"mendeley-speed-bump")
            (mendeley_root / "conflict.jpg").write_bytes(b"conflict")
            conflict_hash = __import__("hashlib").sha256((mendeley_root / "conflict.jpg").read_bytes()).hexdigest()
            holdout = root / "holdout.csv"
            holdout.write_text(f"proposed_label,sha256\nspeed_bump,{conflict_hash}\n", encoding="utf-8")
            output_csv = root / "coverage.csv"
            summary_json = root / "summary.json"
            result = build_manifest(
                svrdd_metadata=metadata_path,
                svrdd_images_root=images_root,
                rtk_images_archive=rtk_images,
                rtk_annotations_archive=rtk_annotations,
                output_csv=output_csv,
                summary_json=summary_json,
                kaggle_speed_bump_audit=kaggle_audit,
                project_root=root,
                mendeley_speed_bump_root=mendeley_root,
                mendeley_conflict_holdout=holdout,
            )
            self.assertEqual(result["sources"]["Kaggle_speed_bump_dataset"]["coverage"]["speed_bump"]["positive_records"], 1)
            self.assertEqual(result["sources"]["Mendeley_Manhole_SpeedBreaker"]["records"], 1)
            with output_csv.open(newline="", encoding="utf-8") as source:
                rows = list(csv.DictReader(source))
            kaggle_row = next(row for row in rows if row["source_dataset"] == "Kaggle_speed_bump_dataset")
            self.assertEqual(kaggle_row["speed_bump_present"], "1")
            self.assertEqual(kaggle_row["pothole_known"], "0")
            self.assertEqual(kaggle_row["pothole_present"], "")


if __name__ == "__main__":
    unittest.main()
