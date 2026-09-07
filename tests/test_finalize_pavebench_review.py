"""Focused checks for finalizing PaveBench human-review decisions."""

import unittest

from src.finalize_pavebench_review import partition_review_rows, validate_review_rows


def row(path: str, decision: str) -> dict[str, str]:
    return {
        "source_category": "longitudinal_crack",
        "source_file": path.rsplit("/", 1)[-1],
        "source_path": path,
        "human_decision": decision,
        "reviewer_note": "",
    }


class FinalizePaveBenchReviewTests(unittest.TestCase):
    def test_complete_review_separates_clear_and_unclear_images(self) -> None:
        rows = [row("train/clear.jpg", "clear_keep"), row("train/unclear.jpg", "unclear_exclude")]
        validate_review_rows(rows)
        clear, excluded = partition_review_rows(rows)
        self.assertEqual([item["source_path"] for item in clear], ["train/clear.jpg"])
        self.assertEqual([item["source_path"] for item in excluded], ["train/unclear.jpg"])

    def test_pending_decision_blocks_finalization(self) -> None:
        with self.assertRaisesRegex(ValueError, "1 image decisions are still pending"):
            validate_review_rows([row("train/pending.jpg", "pending")])

    def test_unknown_decision_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported human_decision"):
            validate_review_rows([row("train/guess.jpg", "probably_crack")])

    def test_duplicate_image_path_is_rejected(self) -> None:
        rows = [row("train/same.jpg", "clear_keep"), row("train/same.jpg", "unclear_exclude")]
        with self.assertRaisesRegex(ValueError, "Duplicate source_path"):
            validate_review_rows(rows)


if __name__ == "__main__":
    unittest.main()
