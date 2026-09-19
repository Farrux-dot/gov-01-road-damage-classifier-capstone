"""Small unit checks for full SRD/ISTD shadow-source audit helpers."""

from __future__ import annotations

import io
import unittest

from PIL import Image

from src.audit_full_shadow_sources import mask_coverage


def image_bytes(values: list[int]) -> bytes:
    image = Image.new("L", (len(values), 1))
    image.putdata(values)
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


class FullShadowAuditTests(unittest.TestCase):
    def test_mask_coverage_counts_non_black_pixels(self) -> None:
        self.assertEqual(mask_coverage(image_bytes([0, 255, 1, 0]), "mask.png"), 0.5)

    def test_mask_coverage_rejects_invalid_data(self) -> None:
        with self.assertRaises(ValueError):
            mask_coverage(b"not an image", "broken.png")


if __name__ == "__main__":
    unittest.main()
