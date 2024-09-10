import logging
from unittest.mock import AsyncMock

from aiohttp import ClientSession
import pytest

from nrk_psapi import NrkPodcastAPI
from nrk_psapi.models.catalog import (
    Episode,
    Podcast,
    PodcastSequential,
    PodcastSeries,
    PodcastStandard,
    SeasonEmbedded,
    SeriesType,
)
from nrk_psapi.models.common import IpCheck

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_request_header(nrk_api):
    assert nrk_api.request_header == {
        "Accept": "application/json",
        "User-Agent": "TestAgent",
    }


@pytest.mark.asyncio
async def test_ipcheck(nrk_api, mock_api_request):
    result = await nrk_api.ipcheck()
    uri, fixture_data = mock_api_request[-1]

    assert uri == fixture_data["_links"]["self"]["href"]
    assert isinstance(result, IpCheck)
    assert result.client_ip_address == fixture_data["data"]["clientIpAddress"]
    assert result.country_code == fixture_data["data"]["countryCode"]


async def test_get_umbrella_podcast(nrk_api, mock_api_request):
    result = await nrk_api.get_podcast("hele_historien")
    uri, fixture_data = mock_api_request[-1]

    assert uri == fixture_data["_links"]["self"]["href"]
    assert isinstance(result, Podcast)
    assert result.series.id == fixture_data["series"]["id"]
    assert result.series_type == SeriesType.UMBRELLA


async def test_get_standard_podcast(nrk_api, mock_api_request):
    result = await nrk_api.get_podcast("tore_sagens_podkast")
    uri, fixture_data = mock_api_request[-1]

    assert uri == fixture_data["_links"]["self"]["href"]
    assert isinstance(result, PodcastStandard)
    assert isinstance(result.series, PodcastSeries)
    assert all(isinstance(item, Episode) for item in result.episodes)
    assert result.series.id == fixture_data["series"]["id"]
    assert result.series_type == SeriesType.STANDARD


async def test_get_sequential_podcast(nrk_api, mock_api_request):
    result = await nrk_api.get_podcast("familiene_paa_orderud")
    uri, fixture_data = mock_api_request[-1]

    assert uri == fixture_data["_links"]["self"]["href"]
    assert isinstance(result, PodcastSequential)
    assert isinstance(result.series, PodcastSeries)
    assert all(isinstance(item, SeasonEmbedded) for item in result.seasons)


@pytest.mark.asyncio
async def test_close(nrk_api):
    nrk_api.session = AsyncMock(spec=ClientSession)
    nrk_api._close_session = True  # noqa: SLF001
    await nrk_api.close()
    nrk_api.session.close.assert_called_once()


@pytest.mark.asyncio
async def test_context_manager():
    async with NrkPodcastAPI() as api:
        assert isinstance(api, NrkPodcastAPI)
    assert api.session is None or api.session.closed
