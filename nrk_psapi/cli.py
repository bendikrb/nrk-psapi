"""nrk-psapi cli tool."""

import argparse
import asyncio
import logging

from rich import print as rprint

from nrk_psapi import NrkPodcastAPI


def main_parser() -> argparse.ArgumentParser:
    """Create the ArgumentParser with all relevant subparsers."""
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser(description='A simple executable to use and test the library.')
    # _add_default_arguments(parser)

    subparsers = parser.add_subparsers(dest='cmd')
    subparsers.required = True

    get_podcasts_parser = subparsers.add_parser('get_all_podcasts', description='Get all podcasts.')
    get_podcasts_parser.set_defaults(func=get_all_podcasts)

    get_podcast_parser = subparsers.add_parser('get_podcast', description='Get podcast(s).')
    get_podcast_parser.add_argument('podcast_id', type=str, nargs="+", help='The podcast id(s).')
    get_podcast_parser.set_defaults(func=get_podcast)

    get_episode_parser = subparsers.add_parser('get_episode', description='Get episode.')
    get_episode_parser.add_argument('podcast_id', type=str, help='The podcast id.')
    get_episode_parser.add_argument('episode_id', type=str, help='The episode id.')
    get_episode_parser.set_defaults(func=get_episode)

    get_episode_manifest_parser = subparsers.add_parser('get_episode_manifest', description='Get episode manifest.')
    get_episode_manifest_parser.add_argument('episode_id', type=str, help='The episode id.')
    get_episode_manifest_parser.set_defaults(func=get_manifest)

    get_episode_metadata_parser = subparsers.add_parser('get_episode_metadata', description='Get episode metadata.')
    get_episode_metadata_parser.add_argument('episode_id', type=str, help='The episode id.')
    get_episode_metadata_parser.set_defaults(func=get_metadata)

    get_curated_podcasts_parser = subparsers.add_parser('get_curated_podcasts', description='Get curated podcasts.')
    get_curated_podcasts_parser.set_defaults(func=get_curated_podcasts)

    return parser


async def get_all_podcasts():
    """Get all podcasts."""
    async with NrkPodcastAPI() as client:
        podcasts = await client.get_all_podcasts()
        rprint(podcasts)


async def get_podcast(args):
    """Get podcast(s)."""
    async with NrkPodcastAPI() as client:
        podcasts = await client.get_podcasts(args.podcast_id)
        for podcast in podcasts:
            rprint(podcast)


async def get_episode(args):
    """Get episode."""
    async with NrkPodcastAPI() as client:
        episode = await client.get_episode(args.podcast_id, args.episode_id)
        rprint(episode)


async def get_manifest(args):
    """Get manifest."""
    async with NrkPodcastAPI() as client:
        manifest = await client.get_playback_manifest(args.episode_id)
        rprint(manifest)


async def get_metadata(args):
    """Get metadata."""
    async with NrkPodcastAPI() as client:
        metadata = await client.get_playback_metadata(args.episode_id)
        rprint(metadata)


async def get_curated_podcasts(args):
    """Get curated podcasts."""
    async with NrkPodcastAPI() as client:
        curated = await client.curated_podcasts()
        for section in curated.sections:
            rprint(f"# {section.title}")
            for podcast in section.podcasts:
                rprint(f"  - {podcast.title} ({podcast.id})")


def main():
    """Run."""
    parser = main_parser()
    args = parser.parse_args()
    asyncio.run(args.func(args))


if __name__ == '__main__':
    main()
