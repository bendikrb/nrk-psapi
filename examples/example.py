# pylint: disable=W0621
"""Asynchronous Python client for the NRK Radio/Podcast APIs."""

import asyncio

from nrk_psapi import NrkPodcastAPI


async def main() -> None:
    """Show example on how to query the Radio Browser API."""
    async with NrkPodcastAPI(user_agent="MyAwesomeApp/1.0.0") as api:

        print("# Get radio pages")
        pages = await api.radio_pages()
        for page in pages.pages:
            print(f"{page.id} ({page.title})")

        print("# Print 10 podcasts starting with 'L'")
        result = await api.browse(letter="L", take=10)
        for podcast in result.series:
            print(f"{podcast.title} ({podcast.type})")

        print("# Print all podcasts")
        result = await api.get_all_podcasts()
        for podcast in result:
            print(f"{podcast.title} ({podcast.type})")

        print("# Get a specific episode")
        print(await api.get_playback_manifest(episode_id="l_9a443e59-5c18-45d8-843e-595c18b5d849"))


if __name__ == "__main__":
    asyncio.run(main())
