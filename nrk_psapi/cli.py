"""nrk-psapi cli tool."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import fields
import logging
import re
from typing import TYPE_CHECKING, Callable

from rich import print as rprint
from rich.box import SIMPLE_HEAD, SQUARE
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from nrk_psapi import NrkPodcastAPI
from nrk_psapi.models.catalog import (
    PodcastSequential,
    PodcastStandard,
    PodcastUmbrella,
)
from nrk_psapi.models.pages import IncludedSection
from nrk_psapi.models.search import (
    Highlight,
    SearchResponseResultsResult,
    SearchResultType,
)

if TYPE_CHECKING:
    from nrk_psapi.models.common import BaseDataClassORJSONMixin


console = Console(width=200)


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

    table = Table(title=title)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    if visible_fields:
        # Render fields in the order specified by visible_fields
        for field_name in visible_fields:
            if hidden_fields and field_name in hidden_fields:
                continue

            field = next(
                (f for f in fields(dataclass_obj) if f.name == field_name), None
            )
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
    ordered_fields = [
        f for f in field_order if f in [field.name for field in dataclass_fields]
    ]
    remaining_fields = [
        f.name for f in dataclass_fields if f.name not in ordered_fields
    ]
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
    result = []
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

    return re.sub(
        r"{([^}]+)}", rf"[{highlight_style}]\1[/{highlight_style}]", final_string
    )


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
    return "\n".join(
        [f"[bold]{h.field}:[/bold] {highlight_context(h.text)}" for h in highlights]
    )


def single_letter(string):
    return string[:1].upper()


def main_parser() -> argparse.ArgumentParser:  # noqa: PLR0915
    """Create the ArgumentParser with all relevant subparsers."""
    parser = argparse.ArgumentParser(
        description="A simple executable to use and test the library."
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Logging verbosity level"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.required = True

    get_podcasts_parser = subparsers.add_parser(
        "get_all_podcasts", description="Get all podcasts."
    )
    get_podcasts_parser.set_defaults(func=get_all_podcasts)

    browse_parser = subparsers.add_parser("browse", description="Browse podcast(s).")
    browse_parser.add_argument(
        "letter", type=single_letter, help="The letter to browse."
    )
    browse_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="The number of results to return per page.",
    )
    browse_parser.add_argument(
        "--page", type=int, default=1, help="The page number to return."
    )
    browse_parser.set_defaults(func=browse)

    get_channel_parser = subparsers.add_parser(
        "get_channel", description="Get channel."
    )
    get_channel_parser.add_argument("channel_id", type=str, help="The channel id.")
    get_channel_parser.set_defaults(func=get_channel)

    get_podcast_parser = subparsers.add_parser(
        "get_podcast", description="Get podcast(s)."
    )
    get_podcast_parser.add_argument(
        "podcast_id", type=str, nargs="+", help="The podcast id(s)."
    )
    get_podcast_parser.set_defaults(func=get_podcast)

    get_podcast_season_parser = subparsers.add_parser(
        "get_podcast_season", description="Get podcast season."
    )
    get_podcast_season_parser.add_argument(
        "podcast_id", type=str, help="The podcast id."
    )
    get_podcast_season_parser.add_argument("season_id", type=str, help="The season id.")
    get_podcast_season_parser.set_defaults(func=get_podcast_season)

    get_podcast_episodes_parser = subparsers.add_parser(
        "get_podcast_episodes", description="Get podcast episodes."
    )
    get_podcast_episodes_parser.add_argument(
        "podcast_id", type=str, help="The podcast id."
    )
    get_podcast_episodes_parser.add_argument(
        "--season_id", type=str, required=False, help="The season id."
    )
    get_podcast_episodes_parser.set_defaults(func=get_podcast_episodes)

    get_series_parser = subparsers.add_parser("get_series", description="Get series.")
    get_series_parser.add_argument("series_id", type=str, help="The series id.")
    get_series_parser.set_defaults(func=get_series)

    get_series_season_parser = subparsers.add_parser(
        "get_series_season", description="Get series season."
    )
    get_series_season_parser.add_argument("series_id", type=str, help="The series id.")
    get_series_season_parser.add_argument("season_id", type=str, help="The season id.")
    get_series_season_parser.set_defaults(func=get_series_season)

    get_episode_parser = subparsers.add_parser(
        "get_episode", description="Get episode."
    )
    get_episode_parser.add_argument("podcast_id", type=str, help="The podcast id.")
    get_episode_parser.add_argument("episode_id", type=str, help="The episode id.")
    get_episode_parser.set_defaults(func=get_episode)

    get_episode_manifest_parser = subparsers.add_parser(
        "get_episode_manifest", description="Get episode manifest."
    )
    get_episode_manifest_parser.add_argument(
        "episode_id", type=str, help="The episode id."
    )
    get_episode_manifest_parser.set_defaults(func=get_manifest)

    get_episode_metadata_parser = subparsers.add_parser(
        "get_episode_metadata", description="Get episode metadata."
    )
    get_episode_metadata_parser.add_argument(
        "episode_id", type=str, help="The episode id."
    )
    get_episode_metadata_parser.set_defaults(func=get_metadata)

    get_curated_podcasts_parser = subparsers.add_parser(
        "get_curated_podcasts", description="Get curated podcasts."
    )
    get_curated_podcasts_parser.set_defaults(func=get_curated_podcasts)

    get_pages_parser = subparsers.add_parser("get_pages", description="Get pages.")
    get_pages_parser.set_defaults(func=get_pages)

    get_page_parser = subparsers.add_parser("get_page", description="Get page content.")
    get_page_parser.add_argument("page_id", type=str, help="The page id.")
    get_page_parser.set_defaults(func=get_page)

    get_page_section_parser = subparsers.add_parser(
        "get_page_section", description="Get page section content."
    )
    get_page_section_parser.add_argument("page_id", type=str, help="The page id.")
    get_page_section_parser.add_argument("section_id", type=str, help="The section id.")
    get_page_section_parser.set_defaults(func=get_page_section)

    get_recommendations_parser = subparsers.add_parser(
        "get_recommendations", description="Get recommendations."
    )
    get_recommendations_parser.add_argument(
        "podcast_id", type=str, help="The podcast id."
    )
    get_recommendations_parser.set_defaults(func=get_recommendations)

    search_parser = subparsers.add_parser("search", description="Search.")
    search_parser.add_argument("query", type=str, help="The search query.")
    search_parser.add_argument("--type", type=SearchResultType, help="The search type.")
    search_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="The number of results to return per page.",
    )
    search_parser.add_argument(
        "--page", type=int, default=1, help="The page number to return."
    )
    search_parser.set_defaults(func=search)

    return parser


# noinspection PyUnusedLocal
async def get_all_podcasts(args):
    """Get all podcasts."""
    async with NrkPodcastAPI() as client:
        podcasts = await client.get_all_podcasts()
        console.print(
            Panel(
                pretty_dataclass_list(
                    podcasts,
                    title="Podcasts",
                    visible_fields=[
                        "series_id",
                        "title",
                        "type",
                        "season_id",
                    ],
                ),
                box=SIMPLE_HEAD,
            )
        )


async def browse(args):
    """Browse podcast(s)."""
    async with NrkPodcastAPI() as client:
        results = await client.browse(args.letter, per_page=args.limit, page=args.page)
        rprint(results)


async def get_channel(args):
    """Get channel."""
    async with NrkPodcastAPI() as client:
        channel = await client.get_live_channel(args.channel_id)
        tables = [
            Panel(
                pretty_dataclass(
                    channel,
                    title="Channel",
                    visible_fields=[
                        "id",
                        "title",
                        "type",
                        "district_channel",
                    ],
                ),
                box=SIMPLE_HEAD,
            ),
            Panel(
                pretty_dataclass_list(
                    channel.entries,
                    title="Entries",
                    visible_fields=[
                        "program_id",
                        "title",
                        "actual_start",
                    ],
                ),
                box=SIMPLE_HEAD,
            ),
        ]
        console.print(*tables)


async def get_podcast(args):
    """Get podcast(s)."""
    async with NrkPodcastAPI() as client:
        podcasts = await client.get_podcasts(args.podcast_id)
        for podcast in podcasts:
            tables = [
                Panel(
                    pretty_dataclass(
                        podcast,
                        title="Podcast",
                        visible_fields=[
                            "type",
                            "series_type",
                            "season_display_type",
                            "titles",
                        ],
                    ),
                    box=SIMPLE_HEAD,
                ),
                Panel(
                    pretty_dataclass(
                        podcast.series,
                        title="Series",
                        visible_fields=["id", "title", "category"],
                    ),
                    box=SIMPLE_HEAD,
                ),
            ]

            if isinstance(podcast, PodcastStandard):
                tables.append(
                    Panel(
                        pretty_dataclass_list(
                            podcast.episodes,
                            title="Episodes",
                            visible_fields=[
                                "episode_id",
                                "date",
                                "titles",
                                "duration",
                            ],
                        ),
                        box=SIMPLE_HEAD,
                    )
                )
                tables.append(
                    Panel(
                        pretty_dataclass_list(
                            podcast.seasons,
                            title="Seasons",
                            visible_fields=[
                                "id",
                                "title",
                            ],
                        ),
                        box=SIMPLE_HEAD,
                    )
                )
            elif isinstance(podcast, (PodcastSequential, PodcastUmbrella)):
                tables.append(
                    Panel(
                        pretty_dataclass_list(
                            podcast.seasons,
                            title="Seasons",
                            visible_fields=[
                                "id",
                                "titles",
                                "episode_count",
                            ],
                        ),
                        box=SIMPLE_HEAD,
                    )
                )
                tables.append(
                    Panel(
                        f"nrk get_podcast_season {podcast.series.id} <id>",
                        title="More info",
                        box=SIMPLE_HEAD,
                    )
                )

            console.print(*tables)


async def get_podcast_season(args):
    """Get podcast season."""
    async with NrkPodcastAPI() as client:
        season = await client.get_podcast_season(args.podcast_id, args.season_id)
        tables = [
            Panel(
                pretty_dataclass(
                    season,
                    title=season.titles.title,
                    visible_fields=["series_type", "episode_count"],
                ),
                box=SIMPLE_HEAD,
            ),
            Panel(
                pretty_dataclass_list(
                    season.episodes,
                    title="Episodes",
                    visible_fields=[
                        "episode_id",
                        "date",
                        "titles",
                        "duration",
                    ],
                ),
                box=SIMPLE_HEAD,
            ),
            Panel(
                f"nrk get_episode {args.podcast_id} {season.episodes[0].episode_id}",
                title="Get episode",
                box=SIMPLE_HEAD,
            ),
        ]
        console.print(*tables)


async def get_podcast_episodes(args):
    """Get podcast episodes."""
    async with NrkPodcastAPI() as client:
        episodes = await client.get_podcast_episodes(args.podcast_id, args.season_id)
        tables = [
            Panel(
                pretty_dataclass_list(
                    episodes,
                    title="Episodes",
                    visible_fields=[
                        "episode_id",
                        "date",
                        "titles",
                        "duration",
                    ],
                ),
                box=SIMPLE_HEAD,
            ),
            Panel(
                f"nrk get_episode {args.podcast_id} {episodes[0].episode_id}",
                title="Get episode",
                box=SIMPLE_HEAD,
            ),
        ]
        console.print(*tables)


async def get_series(args):
    """Get series."""
    async with NrkPodcastAPI() as client:
        podcast = await client.get_series(args.series_id)
        tables = [
            Panel(
                pretty_dataclass(
                    podcast,
                    title="Podcast",
                    visible_fields=[
                        "type",
                        "series_type",
                        "season_display_type",
                        "titles",
                    ],
                ),
                box=SIMPLE_HEAD,
            ),
            Panel(
                pretty_dataclass(
                    podcast.series,
                    title="Series",
                    visible_fields=["id", "title", "category"],
                ),
                box=SIMPLE_HEAD,
            ),
        ]

        if isinstance(podcast, PodcastStandard):
            tables.append(
                Panel(
                    pretty_dataclass_list(
                        podcast.episodes,
                        title="Episodes",
                        visible_fields=[
                            "episode_id",
                            "date",
                            "titles",
                            "duration",
                        ],
                    ),
                    box=SIMPLE_HEAD,
                )
            )
            tables.append(
                Panel(
                    pretty_dataclass_list(
                        podcast.seasons,
                        title="Seasons",
                        visible_fields=[
                            "id",
                            "title",
                        ],
                    ),
                    box=SIMPLE_HEAD,
                )
            )
        elif isinstance(podcast, (PodcastSequential, PodcastUmbrella)):
            tables.append(
                Panel(
                    pretty_dataclass_list(
                        podcast.seasons,
                        title="Seasons",
                        visible_fields=[
                            "id",
                            "titles",
                            "episode_count",
                        ],
                    ),
                    box=SIMPLE_HEAD,
                )
            )
            tables.append(
                Panel(
                    f"nrk get_podcast_season {podcast.series.id} <id>",
                    title="More info",
                    box=SIMPLE_HEAD,
                )
            )

        console.print(*tables)


async def get_series_season(args):
    """Get series season."""
    async with NrkPodcastAPI() as client:
        season = await client.get_series_season(args.series_id, args.season_id)
        tables = [
            Panel(
                pretty_dataclass(
                    season,
                    title=season.titles.title,
                    # visible_fields=["series_type", "episode_count"],
                ),
                box=SIMPLE_HEAD,
            ),
            Panel(
                pretty_dataclass_list(
                    season.episodes,
                    title="Episodes",
                    visible_fields=[
                        "episode_id",
                        "date",
                        "titles",
                        "duration",
                    ],
                ),
                box=SIMPLE_HEAD,
            ),
            Panel(
                f"nrk get_episode {args.series_id} {season.episodes[0].episode_id}",
                title="Get episode",
                box=SIMPLE_HEAD,
            ),
        ]
        console.print(*tables)


async def get_recommendations(args):
    """Get recommendations."""
    async with NrkPodcastAPI() as client:
        recommendations = await client.get_recommendations(args.podcast_id)
        for recommendation in recommendations.recommendations:
            console.print(
                Panel(
                    pretty_dataclass(
                        recommendation,
                        hidden_fields=["_links", "upstream_system_info"],
                        field_formatters={
                            "podcast": lambda d: f"{d.id}: {d.titles}",
                            "podcast_season": lambda d: f"{d.podcast_id} - {d.id}: {d.titles}",
                        },
                    ),
                    box=SIMPLE_HEAD,
                )
            )


async def get_episode(args):
    """Get episode."""
    async with NrkPodcastAPI() as client:
        episode = await client.get_episode(args.podcast_id, args.episode_id)
        if episode is None:
            console.print("Episode not found")
            return
        tables = [
            Panel(
                pretty_dataclass(
                    episode,
                    title=str(episode.titles),
                    hidden_fields=[
                        "_links",
                        "titles",
                        "id",
                    ],
                    field_formatters={
                        "image": lambda images: "\n".join([f"- {i}" for i in images]),
                        "square_image": lambda images: "\n".join(
                            [f"- {i}" for i in images]
                        ),
                    },
                ),
                box=SIMPLE_HEAD,
            ),
            Panel(
                f"nrk get_episode_metadata {episode.episode_id}",
                title="Get metadata",
                box=SIMPLE_HEAD,
            ),
            Panel(
                f"nrk get_episode_manifest {episode.episode_id}",
                title="Get manifest",
                box=SIMPLE_HEAD,
            ),
        ]
        console.print(*tables)


async def get_manifest(args):
    """Get manifest."""
    async with NrkPodcastAPI() as client:
        manifest = await client.get_playback_manifest(args.episode_id)
        tables = [
            Panel(
                pretty_dataclass(
                    manifest,
                    hidden_fields=[
                        "_links",
                    ],
                ),
                box=SIMPLE_HEAD,
            ),
            Panel(
                f"nrk get_episode_metadata {args.episode_id}",
                title="Get metadata",
                box=SIMPLE_HEAD,
            ),
        ]
        console.print(*tables)


async def get_metadata(args):
    """Get metadata."""
    async with NrkPodcastAPI() as client:
        metadata = await client.get_playback_metadata(args.episode_id)
        tables = [
            Panel(
                pretty_dataclass(
                    metadata,
                    hidden_fields=[
                        "_links",
                        "_embedded",
                    ],
                ),
                box=SIMPLE_HEAD,
            ),
            Panel(
                f"nrk get_episode_manifest {args.episode_id}",
                title="Get manifest",
                box=SIMPLE_HEAD,
            ),
        ]
        console.print(*tables)


# noinspection PyUnusedLocal
async def get_curated_podcasts(args):
    """Get curated podcasts."""
    async with NrkPodcastAPI() as client:
        curated = await client.curated_podcasts()
        for section in curated.sections:
            console.print(
                Panel(
                    pretty_dataclass_list(
                        section.podcasts,
                        visible_fields=[
                            "id",
                            "title",
                        ],
                        field_widths={
                            "id": 50,
                            "title": 150,
                        },
                    ),
                    title=f"{section.title} (#{section.id})",
                    box=SQUARE,
                    title_align="left",
                )
            )


# noinspection PyUnusedLocal
async def get_pages(args):
    """Get radio pages."""
    async with NrkPodcastAPI() as client:
        radio_pages = await client.radio_pages()
        console.print(
            Panel(
                pretty_dataclass_list(
                    radio_pages.pages,
                    visible_fields=[
                        "id",
                        "title",
                    ],
                    field_widths={
                        "id": 50,
                        "title": 150,
                    },
                    field_order=["id", "title"],
                ),
                title="Pages",
                box=SQUARE,
                title_align="left",
            )
        )
        # for p in radio_pages.pages:
        #     page = await client.radio_page(p.id)
        #     console.print(Text(f"# {page.title}"))
        #     for section in page.sections:
        #         if isinstance(section, IncludedSection):
        #             for plug in section.included.plugs:
        #                 console.print(plug)


async def get_page(args):
    """Get radio page."""
    async with NrkPodcastAPI() as client:
        page = await client.radio_page(args.page_id)
        console.print(Text(f"# {page.title}"))
        for section in page.sections:
            if isinstance(section, IncludedSection):
                console.print(Text(f"## {section.included.title}"))
                for plug in section.included.plugs:
                    console.print(plug)


async def get_page_section(args):
    """Get radio page."""
    async with NrkPodcastAPI() as client:
        page = await client.radio_page(args.page_id, args.section_id)
        console.print(Text(f"# {page.title}"))
        for section in page.sections:
            if isinstance(section, IncludedSection):
                console.print(Text(f"## {section.included.title}"))
                for plug in section.included.plugs:
                    console.print(plug)


async def search(args):
    """Search."""
    async with NrkPodcastAPI() as client:
        search_results = await client.search(
            args.query, per_page=args.limit, page=args.page, search_type=args.type
        )
        tables = []
        for field in fields(search_results.results):
            field_value: SearchResponseResultsResult = getattr(
                search_results.results, field.name
            )
            if len(field_value.results) > 0:
                # noinspection PyTypeChecker
                res_fields = fields(field_value.results[0])
                console.print([f.name for f in res_fields])
            tables.append(
                Panel(
                    pretty_dataclass_list(
                        field_value.results,
                        title=field.name,
                        hidden_fields=[
                            "id",
                            "type",
                            "images",
                            "square_images",
                            "score",
                            # "highlights",
                            "description",
                            "date",
                            "series_title",
                            "season_id",
                        ],
                        field_formatters={
                            "highlights": lambda x: pretty_highlights(x),
                        },
                        field_widths={
                            "highlights": 50,
                        },
                        field_order=[
                            "id",
                            "episode_id",
                            "series_id",
                            "title",
                            "highlights",
                        ],
                    ),
                    box=SIMPLE_HEAD,
                )
            )
        console.print(*tables)


def main():
    """Run."""
    parser = main_parser()
    args = parser.parse_args()

    if args.debug:
        logging_level = logging.DEBUG
    elif args.verbose:
        logging_level = 50 - (args.verbose * 10)
        if logging_level <= 0:
            logging_level = logging.NOTSET
    else:
        logging_level = logging.ERROR

    logging.basicConfig(
        level=logging_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console)],
    )

    asyncio.run(args.func(args))


if __name__ == "__main__":
    main()
