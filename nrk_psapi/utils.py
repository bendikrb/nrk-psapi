from __future__ import annotations

import re
from typing import TYPE_CHECKING

from aiohttp import ClientSession

from nrk_psapi.const import LOGGER as _LOGGER

if TYPE_CHECKING:
    from yarl import URL

    from nrk_psapi.models import Image


def get_nested_items(data: dict[str, any], items_key: str) -> list[dict[str, any]]:
    """Get nested items from a dictionary based on the provided items_key."""

    items = data
    for key in items_key.split("."):
        items = items.get(key, {})

    if not isinstance(items, list):
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


async def fetch_file_info(url: URL | str, session: ClientSession | None = None) -> tuple[int, str]:
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
    return int(content_length), mime_type
