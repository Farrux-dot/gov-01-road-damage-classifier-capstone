"""Focused checks for the StreetSurfaceVis shadow-review workbook reader."""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from src.finalize_v2_streetsurfacevis_shadow_review import shadow_workbook_rows


class ShadowReviewImportTests(unittest.TestCase):
    def test_reader_keeps_only_shadow_candidate_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workbook = Path(directory) / "review.xlsx"
            with zipfile.ZipFile(workbook, "w") as archive:
                archive.writestr(
                    "xl/sharedStrings.xml",
                    '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                    "<si><t>SHC-001</t></si><si><t>NS-001</t></si></sst>",
                )
                archive.writestr(
                    "xl/worksheets/sheet1.xml",
                    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
                    '<row r="6"><c r="A6" t="s"><v>0</v></c></row>'
                    '<row r="7"><c r="A7" t="s"><v>1</v></c></row>'
                    "</sheetData></worksheet>",
                )
            self.assertEqual(shadow_workbook_rows(workbook), [{"A": "SHC-001"}])


if __name__ == "__main__":
    unittest.main()
