"""Tests for safe direct-image URL handling; no internet request is made."""

from io import BytesIO
from unittest.mock import Mock, patch
import unittest

from PIL import Image

from src.image_source import MAX_DOWNLOAD_BYTES, download_public_image, validate_public_image_url


class _Headers:
    def __init__(self, content_type="image/png", content_length=None):
        self.content_type = content_type
        self.content_length = content_length

    def get_content_type(self):
        return self.content_type

    def get(self, name):
        return self.content_length if name == "Content-Length" else None


class _Response:
    def __init__(self, content, headers):
        self.content = content
        self.headers = headers

    def read(self, _limit):
        return self.content

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def _png_bytes():
    content = BytesIO()
    Image.new("RGB", (8, 8), "gray").save(content, format="PNG")
    return content.getvalue()


class PublicImageUrlTests(unittest.TestCase):
    def test_private_address_is_rejected_before_any_download(self):
        with self.assertRaisesRegex(ValueError, "public internet"):
            validate_public_image_url("http://127.0.0.1/private.png")

    def test_non_http_link_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "http"):
            validate_public_image_url("file:///C:/road.png")

    @patch("src.image_source.validate_public_image_url", return_value="https://example.org/road.png")
    @patch("src.image_source.build_opener")
    def test_readable_png_is_returned_as_a_named_file(self, mocked_opener, _mocked_validate):
        opener = Mock()
        opener.open.return_value = _Response(_png_bytes(), _Headers())
        mocked_opener.return_value = opener

        image_file = download_public_image("https://example.org/road.png")

        self.assertEqual(image_file.name, "image_from_url.png")
        self.assertEqual(image_file.read(8), b"\x89PNG\r\n\x1a\n")

    @patch("src.image_source.validate_public_image_url", return_value="https://example.org/large.jpg")
    @patch("src.image_source.build_opener")
    def test_oversized_response_is_rejected(self, mocked_opener, _mocked_validate):
        opener = Mock()
        opener.open.return_value = _Response(b"", _Headers("image/jpeg", str(MAX_DOWNLOAD_BYTES + 1)))
        mocked_opener.return_value = opener

        with self.assertRaisesRegex(ValueError, "larger than 10 MB"):
            download_public_image("https://example.org/large.jpg")


if __name__ == "__main__":
    unittest.main()
