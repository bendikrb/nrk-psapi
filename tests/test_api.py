import logging
from unittest.mock import AsyncMock

from aiohttp import ClientSession
import pytest

from nrk_psapi import NrkPodcastAPI
from nrk_psapi.models import (
    ChannelPlug,
    Curated,
    CuratedSection,
    Episode,
    EpisodePlug,
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
    PodcastMetadata,
    PodcastMetadataEmbedded,
    PodcastPlug,
    PodcastSeasonPlug,
    PodcastSeries,
    PodcastStandard,
    PodcastUmbrella,
    Section,
    Series,
    SeriesPlug,
    SeriesType,
    StandaloneProgramPlug,
)

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_request_header(nrk_api: NrkPodcastAPI):
    assert nrk_api.request_header == {
        "Accept": "application/json",
        "User-Agent": "TestAgent",
    }


@pytest.mark.asyncio
async def test_ipcheck(nrk_api: NrkPodcastAPI, mock_api_request):
    result = await nrk_api.ipcheck()
    uri, fixture_data = mock_api_request[-1]

    assert uri == fixture_data["_links"]["self"]["href"]
    assert isinstance(result, IpCheck)
    assert result.client_ip_address == fixture_data["data"]["clientIpAddress"]
    assert result.country_code == fixture_data["data"]["countryCode"]


@pytest.mark.asyncio
async def test_get_series(nrk_api: NrkPodcastAPI, mock_api_request):
    series_id = "hele-historien"
    result = await nrk_api.get_series(series_id)
    uri, fixture_data = mock_api_request[-1]

    assert uri == fixture_data["_links"]["self"]["href"]
    assert isinstance(result, Podcast)


@pytest.mark.asyncio
async def test_get_umbrella_podcast(nrk_api: NrkPodcastAPI, mock_api_request):
    result = await nrk_api.get_podcast("hele_historien")
    uri, fixture_data = mock_api_request[-1]

    assert uri == fixture_data["_links"]["self"]["href"]
    assert isinstance(result, PodcastUmbrella)
    assert result.series.id == fixture_data["series"]["id"]
    assert result.series_type == SeriesType.UMBRELLA


@pytest.mark.asyncio
async def test_get_standard_podcast(nrk_api: NrkPodcastAPI, mock_api_request):
    podcast_id = "tore_sagens_podkast"
    result = await nrk_api.get_podcast(podcast_id)
    uri, fixture_data = mock_api_request[-1]

    assert uri == fixture_data["_links"]["self"]["href"]
    assert isinstance(result, PodcastStandard)
    assert isinstance(result.series, PodcastSeries)
    assert all(isinstance(item, Episode) for item in result.episodes)
    assert result.series.id == fixture_data["series"]["id"]
    assert result.series_type == SeriesType.STANDARD


@pytest.mark.asyncio
async def test_get_podcast_episodes(nrk_api: NrkPodcastAPI, mock_api_request):
    podcast_id = "tore_sagens_podkast"
    result = await nrk_api.get_podcast_episodes(podcast_id)

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(item, Episode) for item in result)


@pytest.mark.asyncio
async def test_get_all_podcasts(nrk_api: NrkPodcastAPI, mock_api_request):
    result = await nrk_api.get_all_podcasts()
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(item, Series) for item in result)


@pytest.mark.asyncio
async def test_get_series_type(nrk_api: NrkPodcastAPI, mock_api_request):
    series_id = "hele-historien"
    result = await nrk_api.get_series_type(series_id)
    _, fixture_data = mock_api_request[-1]
    assert isinstance(result, SeriesType)
    assert result == SeriesType.STANDARD
    assert str(result) == fixture_data["seriesType"]


@pytest.mark.asyncio
async def test_get_metadata(nrk_api: NrkPodcastAPI, mock_api_request):
    episode_id = "l_d3d4424e-e692-4ab8-9442-4ee6929ab82a"
    result = await nrk_api.get_playback_metadata(episode_id)
    uri, fixture_data = mock_api_request[-1]
    assert uri == fixture_data["_links"]["self"]["href"]
    assert isinstance(result, PodcastMetadata)
    assert isinstance(result.podcast, PodcastMetadataEmbedded)
    assert isinstance(result.podcast_episode, PodcastEpisodeMetadata)
    assert (
        result.podcast.titles.title
        == fixture_data["_embedded"]["podcast"]["titles"]["title"]
    )
    assert (
        result.podcast_episode.clip_id
        == fixture_data["_embedded"]["podcastEpisode"]["clipId"]
    )
    assert isinstance(result.manifests, list)
    assert all(isinstance(item, Manifest) for item in result.manifests)

@pytest.mark.asyncio
async def test_curated_podcasts(nrk_api: NrkPodcastAPI, mock_api_request):
    result = await nrk_api.curated_podcasts()
    assert isinstance(result, Curated)
    assert isinstance(result.sections, list)
    assert len(result.sections) > 0
    assert all(isinstance(item, CuratedSection) for item in result.sections)


@pytest.mark.asyncio
async def test_pages(nrk_api: NrkPodcastAPI, mock_api_request):
    result = await nrk_api.radio_pages()
    assert isinstance(result, Pages)
    assert all(isinstance(item, PageListItem) for item in result.pages)
    for page in result.pages:
        assert len(page.title) > 0


@pytest.mark.asyncio
async def test_podcast_page(nrk_api: NrkPodcastAPI, mock_api_request):  # noqa: C901
    page_id = "podcast"
    result = await nrk_api.radio_page(page_id)
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


@pytest.mark.asyncio
async def test_close(nrk_api):
    nrk_api.session = AsyncMock(spec=ClientSession)
    nrk_api._close_session = True  # pylint: disable=protected-access  # noqa: SLF001
    await nrk_api.close()
    nrk_api.session.close.assert_called_once()


@pytest.mark.asyncio
async def test_context_manager():
    async with NrkPodcastAPI() as api:
        assert isinstance(api, NrkPodcastAPI)
    assert api.session is None or api.session.closed
