from __future__ import annotations

import re


def get_nested_items(data: dict[str, any], items_key: str) -> list[dict[str, any]]:
    """Get nested items from a dictionary based on the provided items_key."""

    items = data
    for key in items_key.split("."):
        items = items.get(key, {})

    if not isinstance(items, list):
        raise TypeError(f"Expected a list at '{items_key}', but got {type(items)}")

    return items


def sanitize_string(s: str):
    """Sanitize a string to be used as a URL parameter."""

    s = s.lower().replace(' ', '_')
    s = s.replace('æ', 'ae').replace('ø', 'oe').replace('å', 'aa')
    return re.sub(r'^[0-9_]+', '', re.sub(r'[^a-z0-9_]', '', s))[:50].rstrip('_')
