"""Small unit checks for the dependency-free XLSX reader used by the V2 review importer."""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from src.finalize_v2_no_shadow_review import column_letter, workbook_rows


class NoShadowReviewImportTests(unittest.TestCase):
    def test_column_letter_reads_standard_references(self) -> None:
        self.assertEqual(column_letter("F6"), "F")
        self.assertEqual(column_letter("AA10"), "AA")

    def test_workbook_rows_reads_shared_strings_and_ignores_headers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workbook = Path(directory) / "review.xlsx"
            with zipfile.ZipFile(workbook, "w") as archive:
                archive.writestr(
                    "xl/sharedStrings.xml",
                    '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                    "<si><t>NS-001</t></si><si><t>no_shadow_clear</t></si></sst>",
                )
                archive.writestr(
                    "xl/worksheets/sheet1.xml",
                    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
                    '<row r="5"><c r="A5" t="s"><v>1</v></c></row>'
                    '<row r="6"><c r="A6" t="s"><v>0</v></c><c r="F6" t="s"><v>1</v></c></row>'
                    "</sheetData></worksheet>",
                )
            self.assertEqual(workbook_rows(workbook), [{"A": "NS-001", "F": "no_shadow_clear"}])


if __name__ == "__main__":
    unittest.main()
