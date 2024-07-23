from __future__ import annotations


def get_nested_items(data: dict[str, any], items_key: str) -> list[dict[str, any]]:
    """
    Get nested items from a dictionary based on the provided items_key.

    Parameters:
        data (dict[str, any]): The dictionary to extract nested items from.
        items_key (str): The key to access the nested items.

    Returns:
        list[dict[str, any]]: The list of nested items extracted based on the items_key.

    Raises:
        ValueError: If the extracted items are not in list format.
    """
    items = data
    for key in items_key.split("."):
        items = items.get(key, {})

    if not isinstance(items, list):
        raise ValueError(f"Expected a list at '{items_key}', but got {type(items)}")

    return items
