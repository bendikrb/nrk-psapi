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

from .helpers import load_fixture_json


@pytest.mark.parametrize(
    "podcast_id",
    [
        "tore_sagens_podkast",
    ],
)
async def test_build_rss_feed(aresponses: ResponsesMockServer, podcast_id: str):
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
        json_response(data=load_fixture_json(f"radio_catalog_podcast_{podcast_id}_episodes_page1")),
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
        feed = NrkPodcastFeed(nrk_api, "http://example.com")
        rss = await feed.build_podcast_rss(podcast_id, limit=10)

        assert rss.title == "Tore Sagens podkast"
        assert rss.link == f"http://example.com/{podcast_id}"
        assert len(rss.items) == 10

        xml = rss.rss()
        assert len(xml) > 0
