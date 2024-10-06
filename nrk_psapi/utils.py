from __future__ import annotations

import asyncio
from fractions import Fraction
from http import HTTPStatus
from io import BytesIO
import math
import re
from typing import TYPE_CHECKING

from aiohttp import ClientError, ClientResponseError, ClientSession
from PIL import Image as PILImage

from nrk_psapi.const import LOGGER as _LOGGER

if TYPE_CHECKING:
    from yarl import URL

    from nrk_psapi.models import FetchedFileInfo, Image


def get_nested_items(data: dict[str, any], items_key: str) -> list[dict[str, any]]:
    """Get nested items from a dictionary based on the provided items_key."""

    items = data
    for key in items_key.split("."):
        items = items.get(key, {})

    if not isinstance(items, list):  # pragma: no cover
        raise TypeError(f"Expected a list at '{items_key}', but got {type(items)}")

    return items


def get_image(images: list[Image], min_size: int | None = None) -> Image | None:
    candidates = [img for img in images if img.width is not None]
    if min_size is None:
        candidates.sort(key=lambda img: img.width, reverse=True)
        return candidates[0] if candidates else None
    return next((img for img in candidates if img.width >= min_size), None)


def sanitize_string(s: str, delimiter: str = "_"):
    """Sanitize a string to be used as a URL parameter."""

    s = s.lower().replace(" ", delimiter)
    s = s.replace("æ", "ae").replace("ø", "oe").replace("å", "aa")
    return re.sub(rf"^[0-9{delimiter}]+", "", re.sub(rf"[^a-z0-9{delimiter}]", "", s))[:50].rstrip(delimiter)


async def fetch_file_info(url: URL | str, session: ClientSession | None = None) -> FetchedFileInfo:
    """Retrieve content-length and content-type for the given URL."""
    close_session = False
    if session is None:
        session = ClientSession()
        close_session = True

    _LOGGER.debug("Fetching file info from %s", url)
    response = await session.head(url, allow_redirects=True)
    content_length = response.headers.get("Content-Length")
    mime_type = response.headers.get("Content-Type")
    if close_session:
        await session.close()
    return {"content_length": int(content_length), "content_type": mime_type}


def parse_aspect_ratio(ar: str) -> Fraction:
    width, height = map(int, ar.split(":"))
    if width <= 0 or height <= 0:
        raise ValueError("Invalid aspect ratio format. Aspect ratio values must be positive integers")
    if width > 100 or height > 100:  # noqa: PLR2004
        raise ValueError("Invalid aspect ratio format. Aspect ratio values should be reasonable (<=100)")
    return Fraction(width, height)


async def tiled_images(
    image_urls: list[str],
    tile_size: int = 100,
    columns: int = 3,
    aspect_ratio: str | None = None,
    *,
    session: ClientSession | None = None,
) -> bytes:
    """Generate a tiled image from a list of image URLs.

    Args:
        image_urls: List of image URLs to tile.
        tile_size: Size of each tile in pixels.
        columns: Number of columns in the tiled image.
        aspect_ratio: Desired aspect ratio of the resulting image, e.g. "16:9".
            If not provided, the aspect ratio will be a result of the number of image_urls divided by columns.
        session: Optional aiohttp session to use. If not provided, a new session will be created.

    """

    async def process_image(sess, url):
        try:
            async with sess.get(url) as response:
                if response.status == HTTPStatus.OK:
                    data = await response.read()
                    content_type = response.headers.get("Content-Type", "").lower()

                    if "jpeg" in content_type or "jpg" in content_type:
                        return data
                    _LOGGER.warning(f"Unsupported image type from {url}: {content_type}")
                    return None

                _LOGGER.warning(f"Failed to fetch image from {url}. Status code: {response.status}")
                return None
        except (ClientError, ClientResponseError) as e:
            _LOGGER.warning(f"Error processing image from {url}: {e!s}")
            return None

    aspect = None
    if aspect_ratio is not None:
        aspect = parse_aspect_ratio(aspect_ratio)

    close_session = False
    if session is None:
        session = ClientSession()
        close_session = True

    tasks = [process_image(session, url) for url in image_urls]
    images = await asyncio.gather(*tasks)

    if close_session:
        await session.close()

    # Filter out None values (failed image downloads)
    images = [img for img in images if img is not None]

    if aspect_ratio is None:
        rows = math.ceil(len(images) / columns)
        total_tiles = len(images)
    else:
        # Calculate the number of rows needed to match the aspect ratio
        total_tiles = columns * math.ceil(columns * aspect.denominator / aspect.numerator)
        rows = math.ceil(total_tiles / columns)

    # Create a new image to hold the tiles
    result = PILImage.new("RGB", (tile_size * columns, tile_size * rows))

    # Place each image in the grid
    for index, image_data in enumerate(images):
        if aspect_ratio is not None and index >= total_tiles:
            break
        row = index // columns
        col = index % columns
        with PILImage.open(BytesIO(image_data)) as img:
            img.thumbnail((tile_size, tile_size))
            x = col * tile_size
            y = row * tile_size
            result.paste(img, (x, y))

    if aspect_ratio is not None:
        final_height = int(result.width * aspect.denominator / aspect.numerator)
        result = result.crop((0, 0, result.width, final_height))

    # Convert the result to bytes
    output = BytesIO()
    result.save(output, format="JPEG")
    return output.getvalue()
