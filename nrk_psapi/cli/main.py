"""nrk-psapi cli tool."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import fields
import logging

from rich.console import Console
from rich.logging import RichHandler
from rich.syntax import Syntax
from rich.theme import Theme

from nrk_psapi import NrkPodcastAPI, NrkUserLoginDetails, __version__
from nrk_psapi.auth import NrkAuthClient
from nrk_psapi.caching import cache_disabled, clear_cache
from nrk_psapi.cli.utils import (
    _get_client,
    csv_to_list,
    header_panel,
    pretty_dataclass,
    pretty_dataclass_list,
    pretty_highlights,
    pretty_images,
    pretty_list,
    single_letter,
)
from nrk_psapi.exceptions import NrkPsApiNotFoundError
from nrk_psapi.models.catalog import (
    PodcastSequential,
    PodcastStandard,
    PodcastUmbrella,
)
from nrk_psapi.models.pages import IncludedSection
from nrk_psapi.models.search import (
    SearchResponseResultsResult,
    SearchResultType,
)
from nrk_psapi.rss.feed import NrkPodcastFeed

console = Console(width=200, theme=Theme({"error": "bold red", "success": "bold green", "info": "bold blue"}))


def main_parser() -> argparse.ArgumentParser:  # noqa: PLR0915
    """Create the ArgumentParser with all relevant subparsers."""
    parser = argparse.ArgumentParser(description="A simple executable to use and test the library.")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Logging verbosity level")
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s v{__version__}")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-cache", action="store_true", help="Run without using cache")

    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.required = True

    #
    # Login
    #
    login_parser = subparsers.add_parser("login", description="Log in")
    login_parser.add_argument("username", type=str, help="Username / E-mail")
    login_parser.add_argument("password", type=str, help="Password")
    login_parser.set_defaults(func=login)

    #
    # Cache
    #
    cache_parser = subparsers.add_parser("cache_clear", description="Clear the cache.")
    cache_parser.set_defaults(func=cache_clear)

    #
    # Browse
    #
    browse_parser = subparsers.add_parser("browse", description="Browse podcast(s).")
    browse_parser.add_argument(
        "category", type=str, nargs="?", help="Filter by category (corresponds to the ones from 'pages')."
    )
    browse_parser.add_argument("--letter", type=single_letter, help="Filter by letter: A-Z,#")
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
    _add_paging_arguments(podcast_parser)
    podcast_parser.set_defaults(func=get_podcasts)

    #
    # Series
    #
    series_parser = subparsers.add_parser("series", description="Get series.")
    series_parser.add_argument("series_id", type=str, nargs="?", help="Series id.")
    series_parser.add_argument("season_id", type=str, nargs="?", help="Season id.")
    series_parser.add_argument("--episodes", action="store_true", help="Get episodes.")
    _add_paging_arguments(series_parser)
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
    # RSS
    #
    rss_parser = subparsers.add_parser("rss", description="Get RSS feed.")
    rss_parser.add_argument("podcast_id", type=str, help="Podcast id.")
    rss_parser.add_argument("output_path", type=argparse.FileType("w", encoding="utf-8"), help="Output path.")
    rss_parser.add_argument("--base_url", type=str, help="Base URL.")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="The number of episodes to include in the feed. Default is all episodes.",
    )
    rss_parser.set_defaults(func=get_rss_feed)

    #
    # Search
    #
    search_parser = subparsers.add_parser("search", description="Search.")
    search_parser.add_argument("query", type=str, help="Search query.")
    search_parser.add_argument("--type", type=SearchResultType, help="Search type.")
    search_parser.set_defaults(func=search)
    _add_paging_arguments(search_parser)

    #
    # Send message
    #
    send_message_parser = subparsers.add_parser("send-message", description="Send message.")
    send_message_parser.add_argument("message", type=str, help="Message.")
    send_message_parser.add_argument("--podcast_id", type=str, required=True, help="Podcast ID.")
    send_message_parser.add_argument("--anonymous", action="store_true", help="Send anonymously.")
    send_message_parser.add_argument("--phone", type=str, default=None, help="Phone number.")
    send_message_parser.set_defaults(func=send_message)

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


async def login(args):
    """Login."""
    async with NrkAuthClient() as client:
        result = await client.authorize(NrkUserLoginDetails(args.username, args.password))
        console.print(result.state, style="success")
        console.print(result.session.access_token)


async def cache_clear(_args):
    """Clear the cache."""
    clear_cache()
    console.print("Cache cleared", style="info")


async def browse(args):
    """Browse podcast(s)."""
    async with NrkPodcastAPI() as client:
        results = await client.browse(
            category=args.category,
            letter=args.letter,
            per_page=args.limit,
            page=args.page,
        )

        cmd_letter = f" --letter {args.letter}" if args.letter else ""
        title_letter = f" (starting with [bold]{args.letter}[/bold])" if args.letter else ""

        console.print(header_panel(f"{results.title}{title_letter}", f"{results.total_count} results"))
        console.print(
            pretty_dataclass_list(
                results.series,
                visible_fields=[
                    "id",
                    "series_id",
                    "type",
                    "title",
                ],
                field_order=["id", "series_id", "type", "title"],
            ),
        )
        if results.total_count > args.limit * args.page:
            console.print(
                "[cyan]> Next page[/cyan]\n"
                f"$ nrk browse {args.category or ""}{cmd_letter} --limit {args.limit} --page {args.page + 1}\n"
            )
        if results.total_count > 0 and not args.letter:
            console.print(
                "[cyan]> Only get results starting with A[/cyan]\n"
                f"$ nrk browse {args.category or ""} [bold blue]--letter A[/bold blue]\n"
            )
        if results.total_count > 0 and not args.category:
            console.print(
                "[cyan]> Filter by category[/cyan]\n"
                f"$ nrk browse [bold blue]kultur[/bold blue]{cmd_letter}"
            )


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
            else:
                console.print(
                    Syntax(
                        f"$ nrk podcast {podcast.series.id} {podcast.seasons[0].id} --episodes",
                        lexer="bash",
                    )
                )
                console.print(
                    Syntax(
                        f"$ nrk podcast {podcast.series.id} --episodes --limit 50 --page 1",
                        lexer="bash",
                    )
                )


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
            episodes = await client.get_series_episodes(
                args.series_id,
                args.season_id,
                page_size=args.limit,
                page=args.page,
            )
        else:
            episodes = await client.get_podcast_episodes(
                args.podcast_id,
                args.season_id,
                page_size=args.limit,
                page=args.page,
            )

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
        try:
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
        except NrkPsApiNotFoundError:
            console.print(f"Series [bold]{args.series_id}[/bold] not found")
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


async def get_rss_feed(args):
    """Get RSS feed."""

    output_file = args.output_path
    async with NrkPodcastAPI() as client:
        rss = NrkPodcastFeed(client, args.base_url)
        feed = await rss.build_podcast_rss(args.podcast_id, args.limit)
        xml = feed.rss()
        output_file.write(xml)
        console.print(f"Wrote {len(xml)} bytes to {output_file.name}")


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
        total_counts = search_results.total_count
        for field in fields(search_results.results):
            field_value: SearchResponseResultsResult = getattr(search_results.results, field.name)
            if len(field_value.results) > 0:
                console.print(
                    header_panel(
                        field.name,
                        f"[bold]{getattr(total_counts, field.name)}[/bold] results",
                    )
                )
                console.print(
                    pretty_dataclass_list(
                        field_value.results,
                        hidden_fields=[
                            "id",
                            "type",
                            "images",
                            "square_images",
                            "score",
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


async def send_message(args):
    """Send message."""
    async with _get_client(args) as client:
        console.print(
            f"Sending {"anonymous" if args.anonymous else "non-anonymous"} message to [bold]{args.podcast_id}[/bold]:"
        )
        console.print(f"Using phone number: [bold]{args.phone}[/bold]")
        console.print(f"Message: [bold]{args.message}[/bold]")
        await client.send_message(args.podcast_id, args.message, anonymous=args.anonymous, phone=args.phone)


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

    if args.no_cache:
        with cache_disabled():
            asyncio.run(args.func(args))
    else:
        asyncio.run(args.func(args))


if __name__ == "__main__":
    main()
