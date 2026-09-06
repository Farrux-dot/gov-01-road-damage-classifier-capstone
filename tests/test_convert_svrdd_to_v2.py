import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.convert_svrdd_to_v2 import convert_metadata_file, convert_record


def source_record(categories, names):
    return {
        "file_name": "images/example.jpg",
        "region": "Example",
        "image_id": "example-id",
        "width": 1024,
        "height": 1024,
        "objects": {
            "bbox": [[1.0, 2.0, 3.0, 4.0] for _ in categories],
            "bbox_yolo": [[0.5, 0.5, 0.1, 0.1] for _ in categories],
            "categories": categories,
            "category_names": names,
        },
    }


class ConvertSvrddToV2Tests(unittest.TestCase):
    def test_conversion_preserves_boxes_and_adds_v2_outputs(self):
        converted = convert_record(source_record([3, 0, 4, 5], ["pothole", "longitudinal crack", "manhole cover", "longitudinal patch"]))
        self.assertEqual(converted["objects"]["bbox"], [[1.0, 2.0, 3.0, 4.0]] * 4)
        self.assertEqual(converted["objects"]["v2_labels"], ["pothole", "crack", "manhole_cover", "repaired_road"])
        self.assertEqual(converted["multi_class_label"], "pothole")
        self.assertTrue(converted["multi_labels"]["pothole_present"])
        self.assertTrue(converted["multi_labels"]["manhole_cover_present"])

    def test_conversion_rejects_id_name_mismatch(self):
        with self.assertRaisesRegex(ValueError, "category ID/name mismatch"):
            convert_record(source_record([3], ["manhole cover"]))

    def test_file_conversion_writes_jsonl_and_counts_v2_objects(self):
        records = [
            source_record([0], ["longitudinal crack"]),
            source_record([3, 6], ["pothole", "transverse patch"]),
        ]
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            input_path = root / "train.metadata.jsonl"
            output_path = root / "train.v2.jsonl"
            input_path.write_text("".join(json.dumps(item) + "\n" for item in records), encoding="utf-8")
            summary = convert_metadata_file(input_path, output_path)
            output_records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(summary["record_count"], 2)
        self.assertEqual(summary["object_counts_by_v2_label"], {"crack": 1, "pothole": 1, "repaired_road": 1})
        self.assertEqual(output_records[1]["multi_class_label"], "pothole")

    def test_converter_file_can_be_started_using_the_documented_command_style(self):
        script = Path(__file__).parents[1] / "src" / "convert_svrdd_to_v2.py"
        completed = subprocess.run([sys.executable, "-B", str(script), "--help"], capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Convert audited SVRDD", completed.stdout)


if __name__ == "__main__":
    unittest.main()
