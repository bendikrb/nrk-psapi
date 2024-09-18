"""nrk-psapi cli tool."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import fields
import logging
import re
from typing import TYPE_CHECKING, Callable

from rich import print as rprint
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.syntax import Syntax
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
    return Panel(grid)


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


def main_parser() -> argparse.ArgumentParser:
    """Create the ArgumentParser with all relevant subparsers."""
    parser = argparse.ArgumentParser(description="A simple executable to use and test the library.")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Logging verbosity level")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.required = True

    #
    # Browse
    #
    browse_parser = subparsers.add_parser("browse", description="Browse podcast(s).")
    browse_parser.add_argument("letter", type=single_letter, help="The letter to browse: A-Z,#")
    browse_parser.set_defaults(func=browse)
    _add_paging_arguments(browse_parser)

    #
    # Channels
    #
    channel_parser = subparsers.add_parser("channel", description="Get channel.")
    channel_parser.add_argument("channel_id", type=str, help="Channel id.")
    channel_parser.set_defaults(func=get_channel)

    #
    # Podcasts
    #
    podcast_parser = subparsers.add_parser("podcast", description="Get podcast(s).")
    podcast_parser.add_argument("podcast_id", type=str, nargs="?", help="Podcast id.")
    podcast_parser.add_argument("season_id", type=str, nargs="?", help="Season id.")
    podcast_parser.add_argument("--episodes", action="store_true", help="Get episodes.")
    podcast_parser.set_defaults(func=get_podcasts)

    #
    # Series
    #
    series_parser = subparsers.add_parser("series", description="Get series.")
    series_parser.add_argument("series_id", type=str, nargs="?", help="Series id.")
    series_parser.add_argument("season_id", type=str, nargs="?", help="Season id.")
    series_parser.add_argument("--episodes", action="store_true", help="Get episodes.")
    series_parser.set_defaults(func=get_series)

    #
    # Episodes
    #
    episode_parser = subparsers.add_parser("episode", description="Get episode.")
    episode_parser.add_argument("podcast_id", type=str, help="Podcast id.")
    episode_parser.add_argument("episode_id", type=str, help="Episode id.")
    episode_parser.add_argument("--metadata", action="store_true", help="Get episode metadata.")
    episode_parser.add_argument("--manifest", action="store_true", help="Get episode manifest.")
    episode_parser.set_defaults(func=get_episode)

    #
    # Programs
    #
    program_parser = subparsers.add_parser("program", description="Get program.")
    program_parser.add_argument("program_id", type=str, help="Program id.")
    program_parser.add_argument("--metadata", action="store_true", help="Get program metadata.")
    program_parser.add_argument("--manifest", action="store_true", help="Get program manifest.")
    program_parser.set_defaults(func=get_program)

    #
    # Curated podcasts
    #
    curated_podcasts_parser = subparsers.add_parser("curated_podcasts", description="Get curated podcasts.")
    curated_podcasts_parser.set_defaults(func=get_curated_podcasts)

    #
    # Pages
    #
    page_parser = subparsers.add_parser("pages", description="Get page(s)/page section.")
    page_parser.add_argument("page_id", nargs="?", type=str, help="Page id.")
    page_parser.add_argument("section_id", nargs="?", type=str, help="Section id.")
    page_parser.set_defaults(func=get_pages)

    #
    # Recommendations
    #
    recommendations_parser = subparsers.add_parser("recommendations", description="Get recommendations.")
    recommendations_parser.add_argument("podcast_id", type=str, help="Podcast id.")
    recommendations_parser.set_defaults(func=get_recommendations)

    #
    # Search
    #
    search_parser = subparsers.add_parser("search", description="Search.")
    search_parser.add_argument("query", type=str, help="Search query.")
    search_parser.add_argument("--type", type=SearchResultType, help="Search type.")
    search_parser.set_defaults(func=search)
    _add_paging_arguments(search_parser)

    return parser


def _add_paging_arguments(parser: argparse.ArgumentParser) -> None:
    """Add paging arguments."""
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="The number of results to return per page.",
    )
    parser.add_argument("--page", type=int, default=1, help="The page number to return.")


async def browse(args):
    """Browse podcast(s)."""
    async with NrkPodcastAPI() as client:
        results = await client.browse(args.letter, per_page=args.limit, page=args.page)
        rprint(results)


async def get_channel(args):
    """Get channel."""
    async with NrkPodcastAPI() as client:
        channel = await client.get_live_channel(args.channel_id)
        console.print(
            *[
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
                pretty_dataclass_list(
                    channel.entries,
                    title="Entries",
                    visible_fields=[
                        "program_id",
                        "title",
                        "actual_start",
                    ],
                ),
            ]
        )


async def get_podcasts(args):
    """Get podcast(s)."""
    if args.podcast_id and args.season_id:
        await get_podcast_season(args)
    elif args.podcast_id:
        await get_podcast(args)
    else:
        async with NrkPodcastAPI() as client:
            podcasts = await client.get_all_podcasts()
            console.print(
                pretty_dataclass_list(
                    podcasts,
                    title="All podcasts",
                    visible_fields=[
                        "series_id",
                        "title",
                        "type",
                        "season_id",
                    ],
                ),
            )


async def get_podcast(args):
    podcast_ids = csv_to_list(args.podcast_id)
    async with NrkPodcastAPI() as client:
        podcasts = await client.get_podcasts(podcast_ids)
        for podcast in podcasts:
            console.rule(podcast.series.title)
            console.print(
                *[
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
                    pretty_dataclass(
                        podcast.series,
                        title="Series",
                        visible_fields=["id", "title", "category"],
                    ),
                ]
            )

            console.rule("Seasons")
            if isinstance(podcast, PodcastStandard):
                console.print(
                    pretty_dataclass_list(
                        podcast.seasons,
                        visible_fields=[
                            "id",
                            "title",
                        ],
                    )
                )
            elif isinstance(podcast, (PodcastSequential, PodcastUmbrella)):
                console.print(
                    pretty_dataclass_list(
                        podcast.seasons,
                        visible_fields=[
                            "id",
                            "titles",
                            "episode_count",
                        ],
                    )
                )
            if args.episodes:
                console.rule("Episodes")
                await get_podcast_episodes(args)


async def get_podcast_season(args):
    """Get podcast season."""
    async with NrkPodcastAPI() as client:
        podcast_id = csv_to_list(args.podcast_id).pop()
        season = await client.get_podcast_season(podcast_id, args.season_id)
        console.rule(season.titles.title)
        console.print(
            pretty_dataclass(
                season,
                visible_fields=["series_type", "episode_count"],
            ),
        )
        if args.episodes:
            console.rule("Episodes")
            await get_podcast_episodes(args)


async def get_podcast_episodes(args, series=False):
    """Get podcast episodes."""
    async with NrkPodcastAPI() as client:
        if series:
            episodes = await client.get_series_episodes(args.series_id, args.season_id)
        else:
            episodes = await client.get_podcast_episodes(args.podcast_id, args.season_id)

        console.print(
            pretty_dataclass_list(
                episodes,
                visible_fields=[
                    "episode_id",
                    "date",
                    "titles",
                    "duration",
                ],
            ),
        )
        if series:
            console.print(
                Syntax(
                    f"$ nrk program {episodes[0].episode_id}",
                    lexer="bash",
                )
            )
        else:
            console.print(
                Syntax(
                    f"$ nrk episode {args.podcast_id} {episodes[0].episode_id}",
                    lexer="bash",
                )
            )


async def get_series(args):
    """Get series."""
    if args.series_id and args.season_id:
        await get_series_season(args.series_id, args.season_id)
    elif args.series_id:
        async with NrkPodcastAPI() as client:
            podcast = await client.get_series(args.series_id)
            console.print(
                *[
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
                    pretty_dataclass(
                        podcast.series,
                        title="Series",
                        visible_fields=["id", "title", "category"],
                    ),
                ]
            )

            console.rule("Seasons")
            if isinstance(podcast, PodcastStandard):
                console.print(
                    pretty_dataclass_list(
                        podcast.seasons,
                        visible_fields=[
                            "id",
                            "title",
                        ],
                    ),
                )
            elif isinstance(podcast, (PodcastSequential, PodcastUmbrella)):
                console.print(
                    pretty_dataclass_list(
                        podcast.seasons,
                        visible_fields=[
                            "id",
                            "titles",
                            "episode_count",
                        ],
                    ),
                )
    if args.episodes and args.series_id:
        console.rule("Episodes")
        await get_podcast_episodes(args, series=True)


async def get_series_season(series_id: str, season_id: str):
    """Get series season."""
    async with NrkPodcastAPI() as client:
        season = await client.get_series_season(series_id, season_id)
        console.rule(season.titles.title)
        console.print(
            pretty_dataclass(
                season,
                visible_fields=[
                    "name",
                    "titles",
                    "image",
                    "series_id",
                    "series_type",
                    "episode_count",
                ],
                field_formatters={
                    "image": pretty_images,
                },
            ),
        )


async def get_recommendations(args):
    """Get recommendations."""
    async with NrkPodcastAPI() as client:
        recommendations = await client.get_recommendations(args.podcast_id)
        for recommendation in recommendations.recommendations:
            console.print(
                pretty_dataclass(
                    recommendation,
                    hidden_fields=["_links", "upstream_system_info"],
                    field_formatters={
                        "podcast": lambda d: f"{d.id}: {d.titles}",
                        "podcast_season": lambda d: f"{d.podcast_id} - {d.id}: {d.titles}",
                    },
                ),
            )


async def get_episode(args):
    """Get episode."""
    async with NrkPodcastAPI() as client:
        episode = await client.get_episode(args.podcast_id, args.episode_id)
        if episode is None:
            console.print("Episode not found")
            return
        console.rule(episode.titles.title)
        console.print(
            pretty_dataclass(
                episode,
                hidden_fields=[
                    "_links",
                    "titles",
                    "id",
                ],
                field_formatters={
                    "image": pretty_images,
                    "square_image": pretty_images,
                },
            ),
        )
    if args.metadata:
        console.rule("Metadata")
        await get_metadata(args)
    if args.manifest:
        console.rule("Manifest")
        await get_manifest(args)


async def get_program(args):
    """Get program."""
    async with NrkPodcastAPI() as client:
        program = await client.get_program(args.program_id)
        console.rule(str(program.temporal_titles))
        console.print(
            pretty_dataclass(
                program,
                hidden_fields=[
                    "_links",
                    "temporal_titles",
                    "availability",
                    "production_year",
                ],
                field_formatters={
                    "image": pretty_images,
                    "square_image": pretty_images,
                    "index_points": pretty_list,
                },
            ),
        )

    if args.metadata:
        console.rule("Metadata")
        await get_metadata(args)
    if args.manifest:
        console.rule("Manifest")
        await get_manifest(args)


async def get_manifest(args):
    """Get manifest."""
    async with NrkPodcastAPI() as client:
        if "program_id" in args:
            manifest = await client.get_playback_manifest(args.program_id, program=True)
        elif "episode_id" in args:
            manifest = await client.get_playback_manifest(args.episode_id, podcast=True)
        elif "channel_id" in args:
            manifest = await client.get_playback_manifest(args.channel_id, channel=True)
        else:
            raise AttributeError("Unable to determine item_id")
        console.print(
            pretty_dataclass(
                manifest,
                hidden_fields=[
                    "_links",
                    "statistics",
                ],
            ),
        )


async def get_metadata(args: argparse.Namespace):
    """Get metadata."""
    async with NrkPodcastAPI() as client:
        if "program_id" in args:
            metadata = await client.get_playback_metadata(args.program_id, program=True)
        elif "episode_id" in args:
            metadata = await client.get_playback_metadata(args.episode_id, podcast=True)
        elif "channel_id" in args:
            metadata = await client.get_playback_metadata(args.channel_id, channel=True)
        else:
            raise AttributeError("Unable to determine item_id")
        console.print(
            pretty_dataclass(
                metadata,
                hidden_fields=[
                    "_links",
                ],
                field_formatters={
                    "interaction_points": pretty_list,
                    "manifests": pretty_list,
                    "interaction": pretty_list,
                },
            ),
        )


# noinspection PyUnusedLocal
async def get_curated_podcasts(args):
    """Get curated podcasts."""
    async with NrkPodcastAPI() as client:
        curated = await client.curated_podcasts()
        for section in curated.sections:
            console.rule(f"{section.title} (#{section.id})")
            console.print(
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
            )


# noinspection PyUnusedLocal
async def get_pages(args):
    """Get radio page(s)."""
    if args.page_id:
        await get_page(args)
    else:
        async with NrkPodcastAPI() as client:
            radio_pages = await client.radio_pages()
            console.print(
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
            )


async def get_page(args):
    """Get radio page."""
    async with NrkPodcastAPI() as client:
        page = await client.radio_page(args.page_id, args.section_id)
        for section in page.sections:
            if isinstance(section, IncludedSection):
                console.print(header_panel(page.title, section.included.title))
                for plug in section.included.plugs:
                    console.print(plug)


async def search(args):
    """Search."""
    async with NrkPodcastAPI() as client:
        search_results = await client.search(
            args.query, per_page=args.limit, page=args.page, search_type=args.type
        )
        for field in fields(search_results.results):
            field_value: SearchResponseResultsResult = getattr(search_results.results, field.name)
            if len(field_value.results) > 0:
                # noinspection PyTypeChecker
                res_fields = fields(field_value.results[0])
                console.print([f.name for f in res_fields])
            console.print(
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
                        "highlights": pretty_highlights,
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
            )


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
