"""Tests for NrkPodcastAPI."""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock

import aiohttp
from aiohttp.web_response import json_response
from aresponses import ResponsesMockServer
import pytest
from yarl import URL

from nrk_psapi import NrkPodcastAPI
from nrk_psapi.const import PSAPI_BASE_URL
from nrk_psapi.exceptions import (
    NrkPsApiConnectionError,
    NrkPsApiConnectionTimeoutError,
    NrkPsApiError,
    NrkPsApiNotFoundError,
    NrkPsApiRateLimitError,
)
from nrk_psapi.models import (
    Channel,
    ChannelPlug,
    Curated,
    CuratedSection,
    Episode,
    EpisodePlug,
    Included,
    IncludedSection,
    IpCheck,
    LinkPlug,
    Manifest,
    Page,
    PageListItem,
    PagePlug,
    Pages,
    Plug,
    Podcast,
    PodcastEpisodeMetadata,
    PodcastEpisodePlug,
    PodcastManifest,
    PodcastMetadata,
    PodcastMetadataEmbedded,
    PodcastPlug,
    PodcastSearchResponse,
    PodcastSeasonPlug,
    PodcastSeries,
    PodcastStandard,
    PodcastType,
    PodcastUmbrella,
    Program,
    Recommendation,
    SearchedSeries,
    SearchResponse,
    Season,
    Section,
    Series,
    SeriesPlug,
    SeriesType,
    StandaloneProgramPlug,
)

from .helpers import load_fixture_json

logger = logging.getLogger(__name__)


async def test_ipcheck(aresponses: ResponsesMockServer):
    fixture_name = "ipcheck"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        "/ipcheck",
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.ipcheck()
        assert isinstance(result, IpCheck)
        assert result.country_code == fixture["data"]["countryCode"]


@pytest.mark.parametrize(
    "series_id",
    [
        "hele-historien",
    ],
)
async def test_get_series(
    aresponses: ResponsesMockServer,
    series_id: str,
):
    fixture_name = f"radio_catalog_series_{series_id}"
    uri = f"/radio/catalog/series/{series_id}"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        uri,
        "GET",
        json_response(data=fixture),
    )

    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.get_series(series_id)
        assert fixture["_links"]["self"]["href"] == uri
        assert isinstance(result, Podcast)


@pytest.mark.parametrize(
    "podcast_id",
    [
        "hele_historien",
    ],
)
async def test_get_umbrella_podcast(
    aresponses: ResponsesMockServer,
    podcast_id: str,
):
    fixture_name = f"radio_catalog_podcast_{podcast_id}"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        f"/radio/catalog/podcast/{podcast_id}",
        "GET",
        json_response(data=fixture),
    )

    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.get_podcast(podcast_id)

        # assert uri == fixture_data["_links"]["self"]["href"]
        assert isinstance(result, PodcastUmbrella)
        # assert result.series.id == fixture_data["series"]["id"]
        assert result.series_type == SeriesType.UMBRELLA


@pytest.mark.parametrize(
    "podcast_id",
    [
        "tore_sagens_podkast",
    ],
)
async def test_get_standard_podcast(
    aresponses: ResponsesMockServer,
    podcast_id: str,
):
    fixture_name = f"radio_catalog_podcast_{podcast_id}"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        f"/radio/catalog/podcast/{podcast_id}",
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        results = await nrk_api.get_podcasts([podcast_id])
        result = results[0]
        # uri, fixture_data = mock_client_session[-1]
        # assert uri == fixture_data["_links"]["self"]["href"]
        assert isinstance(result, PodcastStandard)
        assert isinstance(result.series, PodcastSeries)
        assert all(isinstance(item, Episode) for item in result.episodes)
        # assert result.series.id == fixture_data["series"]["id"]
        assert result.series_type == SeriesType.STANDARD


@pytest.mark.parametrize(
    "season",
    [
        ("tore_sagens_podkast", None),
        ("tore_sagens_podkast", "2021"),
    ],
)
async def test_get_podcast_episodes(
    aresponses: ResponsesMockServer,
    season: tuple[str, str],
):
    podcast_id, season_id = season
    if season_id is not None:
        uri = f"/radio/catalog/podcast/{podcast_id}/seasons/{season_id}/episodes"
        fixture_name = f"radio_catalog_podcast_{podcast_id}_seasons_{season_id}_episodes"
    else:
        uri = f"/radio/catalog/podcast/{podcast_id}/episodes"
        fixture_name = f"radio_catalog_podcast_{podcast_id}_episodes"

    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        uri,
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.get_podcast_episodes(podcast_id, season_id)
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(item, Episode) for item in result)


@pytest.mark.parametrize(
    "season",
    [
        ("hele_historien", "alene-i-atlanteren"),
    ],
)
async def test_get_podcast_season(
    aresponses: ResponsesMockServer,
    season: tuple[str, str],
):
    podcast_id, season_id = season
    fixture_name = f"radio_catalog_podcast_{podcast_id}_seasons_{season_id}"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        f"/radio/catalog/podcast/{podcast_id}/seasons/{season_id}",
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.get_podcast_season(podcast_id, season_id)
        assert isinstance(result, Season)


async def test_get_all_podcasts(aresponses: ResponsesMockServer):
    fixture_name = "radio_search_categories_podcast"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        "/radio/search/categories/podcast",
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.get_all_podcasts()
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(item, Series) for item in result)


@pytest.mark.parametrize(
    "series_id",
    [
        "hele-historien",
    ],
)
async def test_get_series_type(aresponses: ResponsesMockServer, series_id: str):
    fixture_name = f"radio_catalog_series_{series_id}_type"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        f"/radio/catalog/series/{series_id}/type",
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.get_series_type(series_id)
        assert isinstance(result, SeriesType)
        assert result == SeriesType.STANDARD
        assert str(result) == fixture["seriesType"]


@pytest.mark.parametrize(
    "season",
    [
        ("karsten-og-petra-radio", "200511"),
    ],
)
async def test_get_series_season(
    aresponses: ResponsesMockServer,
    season: tuple[str, str],
):
    series_id, season_id = season
    fixture_name = f"radio_catalog_series_{series_id}_seasons_{season_id}"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        f"/radio/catalog/series/{series_id}/seasons/{season_id}",
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.get_series_season(series_id, season_id)
        assert isinstance(result, Season)
        assert result.type == PodcastType.SERIES
        assert result.series_type == SeriesType.STANDARD


@pytest.mark.parametrize(
    "season",
    [
        ("karsten-og-petra-radio", None),
        ("karsten-og-petra-radio", "200511"),
    ],
)
async def test_get_series_episodes(
    aresponses: ResponsesMockServer,
    season: tuple[str, str],
):
    series_id, season_id = season
    if season_id is not None:
        uri = f"/radio/catalog/series/{series_id}/seasons/{season_id}/episodes"
        fixture_name = f"radio_catalog_series_{series_id}_seasons_{season_id}_episodes"
    else:
        uri = f"/radio/catalog/series/{series_id}/episodes"
        fixture_name = f"radio_catalog_series_{series_id}_episodes"

    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        uri,
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.get_series_episodes(series_id, season_id)
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(item, Episode) for item in result)


@pytest.mark.parametrize(
    "podcast_id",
    [
        "hele_historien",
    ],
)
async def test_get_podcast_type(aresponses: ResponsesMockServer, podcast_id: str):
    fixture_name = f"radio_catalog_podcast_{podcast_id}_type"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        f"/radio/catalog/podcast/{podcast_id}/type",
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.get_podcast_type(podcast_id)
        assert isinstance(result, SeriesType)
        assert result == SeriesType.UMBRELLA
        assert str(result) == fixture["seriesType"]


@pytest.mark.parametrize(
    "item_id",
    [
        "l_81a66a37-853f-48c1-a66a-37853fa8c104",
    ],
)
async def test_get_recommendations(aresponses: ResponsesMockServer, item_id: str):
    fixture_name = f"radio_recommendations_{item_id}"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        f"/radio/recommendations/{item_id}",
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.get_recommendations(item_id)
        assert isinstance(result, Recommendation)


async def test_browse(aresponses: ResponsesMockServer):
    fixture_name = "radio_search_categories_alt-innhold_A"
    uri = "/radio/search/categories/alt-innhold"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        uri,
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.browse(letter="A", per_page=10)
        assert isinstance(result, PodcastSearchResponse)
        assert isinstance(result.series, list)
        assert all(isinstance(item, SearchedSeries) for item in result.series)


async def test_search(aresponses: ResponsesMockServer):
    fixture_name = "radio_search_search_beyer"
    uri = "/radio/search/search"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        uri,
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.search(query="beyer", per_page=10)
        assert isinstance(result, SearchResponse)


async def test_search_suggest(aresponses: ResponsesMockServer):
    fixture_name = "radio_search_search_suggest_bren"
    uri = "/radio/search/search/suggest"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        uri,
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.search_suggest("bren")
        assert isinstance(result, list)
        assert len(result) > 0


@pytest.mark.parametrize(
    "media",
    [
        ("podcast", "l_d3d4424e-e692-4ab8-9442-4ee6929ab82a"),
        ("channel", "p1"),
        ("program", "MDFP01003524"),
        (None, "l_d3d4424e-e692-4ab8-9442-4ee6929ab82a"),
    ],
)
async def test_get_metadata(aresponses: ResponsesMockServer, media: tuple[str, str]):
    media_type, media_id = media
    podcast, channel, program = (media_type == "podcast", media_type == "channel", media_type == "program")
    if media_type is None:
        media_type = "podcast"
    fixture_name = f"playback_metadata_{media_type}_{media_id}"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        f"/playback/metadata/{media_id}",
        "GET",
        json_response(data=fixture),
    )
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        f"/playback/metadata/{media_type}/{media_id}",
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.get_playback_metadata(
            media_id,
            podcast=podcast,
            channel=channel,
            program=program,
        )
        assert isinstance(result, PodcastMetadata)
        if media_type == "podcast":
            assert isinstance(result.podcast, PodcastMetadataEmbedded)
            assert isinstance(result.podcast_episode, PodcastEpisodeMetadata)
            assert result.podcast.titles.title == fixture["_embedded"]["podcast"]["titles"]["title"]
            assert result.podcast_episode.clip_id == fixture["_embedded"]["podcastEpisode"]["clipId"]
        assert isinstance(result.manifests, list)
        assert all(isinstance(item, Manifest) for item in result.manifests)


@pytest.mark.parametrize(
    "media",
    [
        ("podcast", "l_9a443e59-5c18-45d8-843e-595c18b5d849"),
        ("channel", "p1"),
        ("program", "MDFP01003524"),
        (None, "l_9a443e59-5c18-45d8-843e-595c18b5d849"),
    ],
)
async def test_get_manifest(aresponses: ResponsesMockServer, media: tuple[str, str]):
    media_type, media_id = media
    podcast, channel, program = (media_type == "podcast", media_type == "channel", media_type == "program")
    if media_type is None:
        media_type = "podcast"
    fixture_name = f"playback_manifest_{media_type}_{media_id}"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        f"/playback/manifest/{media_id}",
        "GET",
        json_response(data=fixture),
    )
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        f"/playback/manifest/{media_type}/{media_id}",
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.get_playback_manifest(
            media_id,
            podcast=podcast,
            program=program,
            channel=channel,
        )
        assert isinstance(result, PodcastManifest)


@pytest.mark.parametrize(
    "episode",
    [
        ("desken_brenner", "l_8c60be4d-ce0b-41d0-a0be-4dce0b81d01a"),
    ],
)
async def test_get_episode(
    aresponses: ResponsesMockServer,
    episode: tuple[str, str],
):
    podcast_id, episode_id = episode
    fixture_name = f"radio_catalog_podcast_{podcast_id}_episodes_{episode_id}"
    uri = f"/radio/catalog/podcast/{podcast_id}/episodes/{episode_id}"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        uri,
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.get_episode(podcast_id, episode_id)
        assert uri == fixture["_links"]["self"]["href"]
        assert isinstance(result, Episode)


@pytest.mark.parametrize(
    "channel_id",
    [
        "p1",
    ],
)
async def test_get_live_channel(aresponses: ResponsesMockServer, channel_id: str):
    fixture_name = f"radio_channels_livebuffer_{channel_id}"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        f"/radio/channels/livebuffer/{channel_id}",
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.get_live_channel(channel_id)
        assert isinstance(result, Channel)


@pytest.mark.parametrize(
    "program_id",
    [
        "MKTT05000905",
    ],
)
async def test_get_program(aresponses: ResponsesMockServer, program_id: str):
    fixture_name = f"radio_catalog_programs_{program_id}"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        f"/radio/catalog/programs/{program_id}",
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.get_program(program_id)
        assert isinstance(result, Program)


async def test_curated_podcasts(aresponses: ResponsesMockServer):
    fixture_name = "radio_pages_podcast"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        "/radio/pages/podcast",
        "GET",
        json_response(data=fixture),
    )

    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.curated_podcasts()
        assert isinstance(result, Curated)
        assert isinstance(result.sections, list)
        assert len(result.sections) > 0
        assert all(isinstance(item, CuratedSection) for item in result.sections)


async def test_pages(aresponses: ResponsesMockServer):
    fixture_name = "radio_pages"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        "/radio/pages",
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.radio_pages()
        assert isinstance(result, Pages)
        assert all(isinstance(item, PageListItem) for item in result.pages)
        for page in result.pages:
            assert len(page.title) > 0


@pytest.mark.parametrize(
    "page",
    [
        ("podcast", None),
        ("podcast", "damer-som-satte-spor"),
        ("podcast", "nonexistent"),
    ],
)
async def test_podcast_page(aresponses: ResponsesMockServer, page: tuple[str, str]):
    page_id, section_id = page
    fixture_name = f"radio_pages_{page_id}"
    fixture = load_fixture_json(fixture_name)
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        f"/radio/pages/{page_id}",
        "GET",
        json_response(data=fixture),
    )
    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        result = await nrk_api.radio_page(page_id, section_id)
        if section_id == "nonexistent":
            assert result is None
            return

        if section_id is not None:
            assert isinstance(result, Included)
            plugs = result.plugs
        else:
            assert isinstance(result, Page)
            assert isinstance(result.sections, list)
            assert all(isinstance(item, Section) for item in result.sections)
            included_sections = [item for item in result.sections if isinstance(item, IncludedSection)]
            plugs = [plug for section in included_sections for plug in section.included.plugs]
        assert all(isinstance(plug, Plug) for plug in plugs)
        for plug in plugs:
            if isinstance(plug, PagePlug):
                assert len(plug.page.page_id) > 0
            if isinstance(plug, PodcastPlug):
                assert len(plug.title) > 0
            if isinstance(plug, PodcastEpisodePlug):
                assert len(plug.podcast_episode.title) > 0
            if isinstance(plug, PodcastSeasonPlug):
                assert len(plug.podcast_season.podcast_season_title) > 0
            if isinstance(plug, SeriesPlug):
                assert len(plug.series.title) > 0
                assert len(plug.id) > 0
            if isinstance(plug, EpisodePlug):
                assert len(plug.id) > 0
                assert len(plug.series_id) > 0
                assert len(plug.episode.title) > 0
            if isinstance(plug, LinkPlug):
                assert len(str(plug.link)) > 0
            if isinstance(plug, ChannelPlug):
                assert len(plug.id) > 0
                assert len(plug.channel.title) > 0
            if isinstance(plug, StandaloneProgramPlug):
                assert len(plug.id) > 0
                assert len(plug.program.title) > 0


async def test_internal_session(aresponses: ResponsesMockServer):
    """Test JSON response is handled correctly."""
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        "/ipcheck",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"status": "ok"}',
        ),
    )
    async with NrkPodcastAPI() as nrk_api:
        response = await nrk_api._request("ipcheck")
        assert response == {"status": "ok"}


async def test_timeout(aresponses: ResponsesMockServer):
    """Test request timeout."""

    # Faking a timeout by sleeping
    async def response_handler(_: aiohttp.ClientResponse):
        """Response handler for this test."""
        await asyncio.sleep(2)
        return aresponses.Response(body="Helluu")

    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        "/ipcheck",
        "GET",
        response_handler,
    )

    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session, request_timeout=1)
        with pytest.raises((NrkPsApiConnectionError, NrkPsApiConnectionTimeoutError)):
            assert await nrk_api._request("ipcheck")


async def test_http_error400(aresponses: ResponsesMockServer):
    """Test HTTP 400 response handling."""
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        "/ipcheck",
        "GET",
        aresponses.Response(text="Wtf", status=400),
    )

    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        with pytest.raises(NrkPsApiError):
            assert await nrk_api._request("ipcheck")


async def test_http_error404(aresponses: ResponsesMockServer):
    """Test HTTP 404 response handling."""
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        "/ipcheck",
        "GET",
        aresponses.Response(text="Not found", status=404),
    )

    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        with pytest.raises(NrkPsApiNotFoundError):
            assert await nrk_api._request("ipcheck")


async def test_http_error429(aresponses: ResponsesMockServer):
    """Test HTTP 429 response handling."""
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        "/ipcheck",
        "GET",
        aresponses.Response(text="Too many requests", status=429),
    )

    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        with pytest.raises(NrkPsApiRateLimitError):
            assert await nrk_api._request("ipcheck")


async def test_unexpected_response(aresponses: ResponsesMockServer):
    """Test unexpected response handling."""
    aresponses.add(
        URL(PSAPI_BASE_URL).host,
        "/ipcheck",
        "GET",
        aresponses.Response(text="Success", status=200),
    )

    async with aiohttp.ClientSession() as session:
        nrk_api = NrkPodcastAPI(session=session)
        with pytest.raises(NrkPsApiError):
            assert await nrk_api._request("ipcheck")


async def test_close():
    nrk_api = NrkPodcastAPI()
    nrk_api.session = AsyncMock(spec=aiohttp.ClientSession)
    nrk_api._close_session = True  # pylint: disable=protected-access
    await nrk_api.close()
    nrk_api.session.close.assert_called_once()


async def test_context_manager():
    async with NrkPodcastAPI() as api:
        assert isinstance(api, NrkPodcastAPI)
    assert api.session is None or api.session.closed
