"""Read a single public JPG or PNG from a direct URL for app inference."""

from __future__ import annotations

from io import BytesIO
import ipaddress
from pathlib import Path
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
import warnings

from PIL import Image, UnidentifiedImageError


MAX_DOWNLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}


class _NoRedirects(HTTPRedirectHandler):
    """Do not follow a redirect to an address that was not checked."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _is_public_address(value: str) -> bool:
    address = ipaddress.ip_address(value)
    return address.is_global


def validate_public_image_url(image_url: str) -> str:
    """Return a checked direct URL or raise a user-facing ValueError."""
    parsed = urlparse(image_url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Enter a complete public http:// or https:// image link.")
    if parsed.username or parsed.password:
        raise ValueError("Image links must not include a username or password.")

    hostname = parsed.hostname
    if not hostname or hostname.lower() == "localhost":
        raise ValueError("The image link must use a public internet address.")

    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(hostname, None)}
    except socket.gaierror as exc:
        raise ValueError("The image link could not be found. Check the address and try again.") from exc

    if not addresses or any(not _is_public_address(address) for address in addresses):
        raise ValueError("The image link must use a public internet address.")
    return parsed.geturl()


def _extension_for_content_type(content_type: str) -> str:
    return ".png" if content_type == "image/png" else ".jpg"


def download_public_image(image_url: str) -> BytesIO:
    """Download, size-check, and decode one direct public JPEG or PNG URL."""
    checked_url = validate_public_image_url(image_url)
    request = Request(
        checked_url,
        headers={
            "Accept": "image/jpeg,image/png",
            "User-Agent": "GOV-01-road-condition-checker/1.0",
        },
    )

    try:
        with build_opener(_NoRedirects()).open(request, timeout=10) as response:
            content_type = response.headers.get_content_type().lower()
            if content_type not in ALLOWED_CONTENT_TYPES:
                raise ValueError("That link did not return a JPG or PNG image. Use the image's direct file link.")

            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    too_large = int(content_length) > MAX_DOWNLOAD_BYTES
                except ValueError:
                    too_large = False
                if too_large:
                    raise ValueError("That image is larger than 10 MB. Choose a smaller JPG or PNG.")

            content = response.read(MAX_DOWNLOAD_BYTES + 1)
    except HTTPError as exc:
        if 300 <= exc.code < 400:
            raise ValueError("Use the final direct image link, not a redirect or web-page link.") from exc
        raise ValueError(f"The image link returned HTTP {exc.code}. Check that it is public.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ValueError("The image could not be downloaded. Check the public direct image link.") from exc

    if len(content) > MAX_DOWNLOAD_BYTES:
        raise ValueError("That image is larger than 10 MB. Choose a smaller JPG or PNG.")

    image_file = BytesIO(content)
    image_file.name = f"image_from_url{_extension_for_content_type(content_type)}"
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(image_file) as image:
                image.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError("The link did not contain a safe, readable JPG or PNG image.") from exc

    image_file.seek(0)
    return image_file
