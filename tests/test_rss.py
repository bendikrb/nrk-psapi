"""Tests for nrk_psapi rss."""

from __future__ import annotations

import math
import re

from aiohttp import ClientSession
from aiohttp.web_response import json_response
from aresponses import ResponsesMockServer
import pytest
from yarl import URL

from nrk_psapi import NrkPodcastAPI, NrkPodcastFeed
from nrk_psapi.const import PSAPI_BASE_URL
from nrk_psapi.models.rss import EpisodeChapter  # noqa: TCH001

from .helpers import load_fixture_json


@pytest.mark.parametrize(
    "podcast_id",
    [
        "tore_sagens_podkast",
    ],
)
async def test_build_rss_feed(aresponses: ResponsesMockServer, podcast_id: str):
    episodes_fixture = load_fixture_json(f"radio_catalog_podcast_{podcast_id}_episodes_page1")
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        f"/radio/catalog/podcast/{podcast_id}",
        "GET",
        json_response(data=load_fixture_json(f"radio_catalog_podcast_{podcast_id}")),
    )
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        f"/radio/catalog/podcast/{podcast_id}/episodes",
        "GET",
        json_response(data=episodes_fixture),
    )
    for x, episode in enumerate(episodes_fixture["_embedded"]["episodes"]):
        episode_data = episode.copy()
        episode_data["duration"] = {
            "seconds": 0,
            "iso8601": episode["duration"],
            "displayValue": "1 t 30 min",
        }
        episode_data["contributors"] = [
            {
                "role": "Programleder",
                "name": ["Tore Sagen"] if x < 2 else "Tore Sagen",
            }
        ]
        if x < 2:
            episode_data["indexPoints"] = [
                {"title": "Chapter 1", "startPoint": "PT1M56S", "partId": 0},
                {"title": "Chapter 2", "startPoint": "PT5M44S", "partId": 0},
            ]
        aresponses.add(
            URL(PSAPI_BASE_URL).host,
            f"/radio/catalog/podcast/{podcast_id}/episodes/{episode_data["episodeId"]}",
            "GET",
            json_response(data=episode_data),
            repeat=math.inf,
        )
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        re.compile(r"/playback/manifest/podcast/.*"),
        "GET",
        json_response(
            data=load_fixture_json("playback_manifest_podcast_l_9a443e59-5c18-45d8-843e-595c18b5d849")
        ),
        repeat=math.inf,
    )
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        re.compile(r"/playback/metadata/podcast/.*"),
        "GET",
        json_response(
            data=load_fixture_json("playback_metadata_podcast_l_d3d4424e-e692-4ab8-9442-4ee6929ab82a")
        ),
        repeat=math.inf,
    )
    aresponses.add(
        "podkast.nrk.no",
        re.compile(r"/fil/.*"),
        "HEAD",
        aresponses.Response(
            headers={
                "Content-Length": "107587411",
                "Content-Type": "audio/mpeg",
            },
        ),
        repeat=math.inf,
    )

    async with ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session, enable_cache=False)
        feed = NrkPodcastFeed(
            nrk_api,
            "http://example.com",
            rss_url_suffix=".rss",
        )
        rss = await feed.build_podcast_rss(podcast_id, limit=10)

        assert rss.title == "Tore Sagens podkast"
        assert rss.link == f"http://example.com/{podcast_id}.rss"
        assert len(rss.items) == 10

        xml = rss.rss()
        assert len(xml) > 0

        episode_id = episodes_fixture["_embedded"]["episodes"][0]["episodeId"]
        episode = await nrk_api.get_episode(podcast_id, episode_id)
        chapters: list[EpisodeChapter] = await feed.build_episode_chapters(episode)
        assert len(chapters) == 2
        assert all(isinstance(c, dict) for c in chapters)
