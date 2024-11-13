"""nrk-psapi cli utils."""

from __future__ import annotations

import contextlib
from dataclasses import fields
import re
from typing import TYPE_CHECKING, Callable

from rich.box import SIMPLE
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from nrk_psapi import NrkAuthClient, NrkPodcastAPI, NrkUserLoginDetails

if TYPE_CHECKING:
    from nrk_psapi.models.common import BaseDataClassORJSONMixin
    from nrk_psapi.models.search import Highlight


# noinspection PyTypeChecker
def pretty_dataclass(  # noqa: PLR0912
    dataclass_obj: BaseDataClassORJSONMixin,
    field_formatters: dict[str, Callable[[any], any]] | None = None,
    hidden_fields: list[str] | None = None,
    visible_fields: list[str] | None = None,
    title: str | None = None,
    hide_none: bool = True,
    hide_default: bool = True,
) -> Table:
    """Render a dataclass object in a pretty format using rich."""

    field_formatters = field_formatters or {}
    hidden_fields = hidden_fields or []
    visible_fields = visible_fields or []

    table = Table(title=title, show_header=False, title_justify="left")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    if visible_fields:
        # Render fields in the order specified by visible_fields
        for field_name in visible_fields:
            if hidden_fields and field_name in hidden_fields:
                continue

            field = next((f for f in fields(dataclass_obj) if f.name == field_name), None)
            if not field:
                continue

            field_value = getattr(dataclass_obj, field_name)

            if hide_none and field_value is None:
                continue

            if hide_none and isinstance(field_value, list) and len(field_value) == 0:
                continue

            if hide_default and field_value == field.default:
                continue

            if field_name in field_formatters:
                field_value = field_formatters[field_name](field_value)
            table.add_row(field_name, str(field_value))
    else:
        # Render all fields (except hidden ones) in the default order
        for field in fields(dataclass_obj):
            if hidden_fields and field.name in hidden_fields:
                continue

            field_value = getattr(dataclass_obj, field.name)

            if hide_none and field_value is None:
                continue

            if hide_none and isinstance(field_value, list) and len(field_value) == 0:
                continue

            if hide_default and field_value == field.default:
                continue

            if field.name in field_formatters:
                field_value = field_formatters[field.name](field_value)
            table.add_row(field.name, str(field_value))

    return table


# noinspection PyTypeChecker
def pretty_dataclass_list(  # noqa: PLR0912
    dataclass_objs: list[BaseDataClassORJSONMixin],
    field_formatters: dict[str, Callable[[any], any]] | None = None,
    hidden_fields: list[str] | None = None,
    visible_fields: list[str] | None = None,
    field_widths: dict[str, int] | None = None,
    field_order: list[str] | None = None,
    title: str | None = None,
    hide_none: bool = True,
    hide_default: bool = True,
) -> Table | Text:
    """Render a list of dataclass objects in a table format using rich."""

    field_formatters = field_formatters or {}
    hidden_fields = hidden_fields or []
    visible_fields = visible_fields or []
    field_widths = field_widths or {}
    field_order = field_order or []

    if not dataclass_objs:
        if title is not None:
            return Text(f"{title}: No results")
        return Text("No results")

    dataclass_fields = list(fields(dataclass_objs[0]))
    ordered_fields = [f for f in field_order if f in [field.name for field in dataclass_fields]]
    remaining_fields = [f.name for f in dataclass_fields if f.name not in ordered_fields]
    fields_to_render = ordered_fields + remaining_fields

    table = Table(title=title, expand=True)

    for field_name in fields_to_render:
        if hidden_fields and field_name in hidden_fields:
            continue

        if visible_fields and field_name not in visible_fields:
            continue

        table.add_column(
            field_name,
            style="cyan",
            no_wrap=not field_widths.get(field_name, None),
            width=field_widths.get(field_name, None),
        )

    for obj in dataclass_objs:
        row = []
        for field_name in fields_to_render:
            if hidden_fields and field_name in hidden_fields:
                continue

            if visible_fields and field_name not in visible_fields:
                continue

            field = next((f for f in fields(obj) if f.name == field_name), None)
            if not field:
                continue

            field_value = getattr(obj, field_name)

            if hide_none and field_value is None:
                continue

            if hide_default and field_value == field.default:
                continue

            if field_name in field_formatters:
                field_value = field_formatters[field_name](field_value)
            row.append(str(field_value))
        table.add_row(*row)

    return table


def header_panel(title: str, subtitle: str):
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="right")
    grid.add_row(
        title,
        subtitle,
    )
    return Panel(
        grid,
        style="white on black",
        box=SIMPLE,
    )


def highlight_context(
    text: str,
    highlight_style: str = "italic red",
    max_length=100,
    word_occurrences=2,
) -> str:
    # Find all highlighted words
    highlights = [(m.start(), m.end()) for m in re.finditer(r"\{.*?}", text)]

    if not highlights:
        return text[:max_length] + "..." if len(text) > max_length else text

    # Determine the context to include around each highlight
    result: list[tuple] = []
    current_length = 0
    included_occurrences = 0

    for start, end in highlights:
        if included_occurrences >= word_occurrences:
            break

        # Calculate the context around the highlight
        context_start = max(0, start - (max_length // 4))
        context_end = min(len(text), end + (max_length // 4))

        # Adjust to nearest word boundaries
        if context_start > 0:
            context_start = text.rfind(" ", 0, context_start) + 1
        if context_end < len(text):
            context_end = text.find(" ", context_end)
            if context_end == -1:
                context_end = len(text)

        # Add ellipses if needed
        if result and context_start > result[-1][1]:
            result.append((result[-1][1], context_start))

        result.append((context_start, context_end))
        current_length += context_end - context_start
        included_occurrences += 1  # noqa: SIM113

        if current_length >= max_length:
            break

    # Build the final string
    final_string = ""
    for i, (start, end) in enumerate(result):
        if i > 0:
            final_string += "..."
        final_string += text[start:end]

    return re.sub(r"{([^}]+)}", rf"[{highlight_style}]\1[/{highlight_style}]", final_string)


def bold_and_truncate(text, max_length=100, context_words=2, word_occurrences=3):
    """Bolds words enclosed in curly braces and truncates the text."""
    occurrences = 0
    result = []
    last_end = 0

    for match in re.finditer(r"{([^}]+)}", text):
        if occurrences >= word_occurrences:
            break
        occurrences += 1  # noqa: SIM113
        start = max(0, match.start() - context_words)
        end = min(len(text), match.end() + context_words)

        result.append(text[last_end:start])
        result.append(f"[bold]{match.group(1)}[/bold]")
        last_end = end

    result.append(text[last_end:])
    result = "".join(result)
    return result[:max_length]


def pretty_highlights(highlights: list[Highlight]) -> str:
    return "\n".join([f"[bold]{h.field}:[/bold] {highlight_context(h.text)}" for h in highlights])


def pretty_images(images: list) -> str:
    return "\n".join([f"- {i} ({i.width}px)" for i in images])


def pretty_list(items: list) -> str:
    return "\n".join([f"- {i}" for i in items])


def single_letter(string):
    return string[:1].upper()


def csv_to_list(csv: str) -> list[str]:
    return [x.strip() for x in csv.split(",")]


@contextlib.asynccontextmanager
async def _get_client(args) -> NrkPodcastAPI:
    """Return NrkPodcastAPI based on args."""
    login_details = None
    if hasattr(args, "username") and hasattr(args, "password"):
        login_details = NrkUserLoginDetails(args.username, args.password)
    auth_client = NrkAuthClient(login_details=login_details)
    client = NrkPodcastAPI(auth_client=auth_client)
    try:
        await client.__aenter__()
        yield client
    finally:
        await client.__aexit__(None, None, None)
