"""nrk-psapi."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
import socket

from aiohttp.client import ClientError, ClientResponseError, ClientSession
from aiohttp.hdrs import METH_GET
import async_timeout
import orjson
from yarl import URL

from .const import LOGGER as _LOGGER, PSAPI_BASE_URL
from .exceptions import (
    NrkPsApiConnectionError,
    NrkPsApiConnectionTimeoutError,
    NrkPsApiError,
    NrkPsApiNotFoundError,
    NrkPsApiRateLimitError,
)
from .models.catalog import (
    Episode,
    Podcast,
    Program,
    Season,
    Series,
    SeriesType,
)
from .models.channels import Channel
from .models.common import IpCheck
from .models.metadata import PodcastMetadata
from .models.pages import (
    Curated,
    CuratedPodcast,
    CuratedSection,
    Included,
    IncludedSection,
    Page,
    Pages,
    PodcastPlug,
)
from .models.playback import PodcastManifest
from .models.recommendations import Recommendation, RecommendationContext
from .models.search import (
    PodcastSearchResponse,
    SearchResponse,
    SearchResultStrType,
    SearchResultType,
    SingleLetter,
)
from .utils import fetch_file_info, get_nested_items, sanitize_string


@dataclass
class NrkPodcastAPI:
    """NrkPodcastAPI.

    :param user_agent: User agent string
    :param request_timeout: Request timeout in seconds, defaults to 8
    :param session: Optional web session to use for requests
    :type session: ClientSession, optional
    """

    user_agent: str | None = None

    request_timeout: int = 8
    session: ClientSession | None = None

    _close_session: bool = False

    @property
    def request_header(self) -> dict[str, str]:
        """Generate a header for HTTP requests to the server."""
        return {
            "Accept": "application/json",
            "User-Agent": self.user_agent or "NrkPodcastAPI/1.0.0",
        }

    async def _request_paged_all(
        self,
        uri: str,
        method: str = METH_GET,
        items_key: str | None = None,
        **kwargs,
    ) -> list:
        """Make a paged request."""
        results = []
        page = 1
        page_size = 50

        while True:
            data = await self._request_paged(uri, method, page_size=page_size, page=page, **kwargs)

            items = get_nested_items(data, items_key)
            results.extend(items)

            if "_links" in data and "next" in data["_links"]:
                page += 1
            else:
                break

        return results

    async def _request_paged(
        self,
        uri: str,
        method: str = METH_GET,
        page_size: int = 50,
        page: int = 1,
        **kwargs,
    ):
        """Make a paged request."""
        return await self._request(uri, method, params={"pageSize": page_size, "page": page}, **kwargs)

    async def _request(
        self,
        uri: str,
        method: str = METH_GET,
        **kwargs,
    ) -> str | dict[any, any] | list[any] | None:
        """Make a request."""
        url = URL(PSAPI_BASE_URL).join(URL(uri))
        _LOGGER.debug("Executing %s API request to %s.", method, url)
        headers = kwargs.get("headers")
        headers = self.request_header if headers is None else dict(headers)

        _LOGGER.debug("With headers: %s", headers)
        if self.session is None:
            self.session = ClientSession()
            _LOGGER.debug("New session created.")
            self._close_session = True

        params = kwargs.get("params")
        if params is not None:
            kwargs.update(params={k: v for k, v in params.items() if v is not None})

        try:
            async with async_timeout.timeout(self.request_timeout):
                response = await self.session.request(
                    method,
                    url,
                    **kwargs,
                    headers=headers,
                )
                response.raise_for_status()
        except asyncio.TimeoutError as exception:
            raise NrkPsApiConnectionTimeoutError(
                "Timeout occurred while connecting to NRK API"
            ) from exception
        except (
            ClientError,
            ClientResponseError,
            socket.gaierror,
        ) as exception:
            if exception.status == HTTPStatus.TOO_MANY_REQUESTS:
                raise NrkPsApiRateLimitError("Too many requests to NRK API. Try again later.") from exception
            if exception.status == HTTPStatus.NOT_FOUND:
                raise NrkPsApiNotFoundError("Resource not found") from exception
            msg = f"Error occurred while communicating with NRK API: {exception}"
            raise NrkPsApiConnectionError(msg) from exception

        content_type = response.headers.get("Content-Type", "")
        text = await response.text()
        if "application/json" not in content_type:
            msg = "Unexpected response from the NRK API"
            raise NrkPsApiError(
                msg,
                {"Content-Type": content_type, "response": text},
            )
        return orjson.loads(text)

    async def ipcheck(self) -> IpCheck:
        """Check if IP is blocked.

        :rtype: IpCheck
        """
        result = await self._request("ipcheck")
        return IpCheck.from_dict(result["data"])

    async def get_playback_manifest(
        self,
        item_id: str,
        *,
        podcast=False,
        program=False,
        channel=False,
    ) -> PodcastManifest:
        """Get the manifest for an episode/program/channel.

        :param item_id: Media id
        :param channel: Media is a channel
        :param program: Media is a program
        :param podcast: Media is a podcast
        :rtype: PodcastManifest
        """
        if podcast:
            endpoint = "/podcast"
        elif program:
            endpoint = "/program"
        elif channel:
            endpoint = "/channel"
        else:
            endpoint = ""
        result = await self._request(f"playback/manifest{endpoint}/{item_id}")
        return PodcastManifest.from_dict(result)

    async def get_playback_metadata(
        self,
        item_id: str,
        *,
        podcast=False,
        program=False,
        channel=False,
    ) -> PodcastMetadata:
        """Get the metadata for an episode/program/channel.

        :param item_id: Media id
        :param channel: Media is a channel
        :param program: Media is a program
        :param podcast: Media is a podcast
        :rtype: PodcastMetadata
        """
        if podcast:
            endpoint = "/podcast"
        elif program:
            endpoint = "/program"
        elif channel:
            endpoint = "/channel"
        else:
            endpoint = ""
        result = await self._request(f"playback/metadata{endpoint}/{item_id}")
        return PodcastMetadata.from_dict(result)

    async def get_episode(self, podcast_id: str, episode_id: str) -> Episode:
        """Get episode.

        :param podcast_id:
        :param episode_id:
        :rtype: Episode
        """
        result = await self._request(f"radio/catalog/podcast/{podcast_id}/episodes/{episode_id}")
        return Episode.from_dict(result)

    async def get_series_type(self, series_id: str) -> SeriesType:
        """Get series type.

        :param series_id:
        :rtype: SeriesType
        """
        result = await self._request(f"radio/catalog/series/{series_id}/type")
        return SeriesType.from_str(result["seriesType"])

    async def get_podcast_type(self, podcast_id: str) -> SeriesType:
        """Get podcast type.

        :param podcast_id:
        :rtype: SeriesType
        """
        result = await self._request(f"radio/catalog/podcast/{podcast_id}/type")
        return SeriesType.from_str(result["seriesType"])

    async def get_series_season(self, series_id: str, season_id: str) -> Season:
        """Get series season.

        :param series_id:
        :param season_id:
        :rtype: Season
        """
        result = await self._request(f"radio/catalog/series/{series_id}/seasons/{season_id}")
        return Season.from_dict(result)

    async def get_series_episodes(self, series_id: str, season_id: str | None = None) -> list[Episode]:
        """Get series episodes.

        :param series_id:
        :param season_id:
        :rtype: list[Episode]
        """
        if season_id is not None:
            uri = f"radio/catalog/series/{series_id}/seasons/{season_id}/episodes"
        else:
            uri = f"radio/catalog/series/{series_id}/episodes"
        result = await self._request_paged_all(
            uri,
            items_key="_embedded.episodes",
        )
        return [Episode.from_dict(e) for e in result]

    async def get_live_channel(self, channel_id: str) -> Channel:
        """Get live channel.

        :param channel_id:
        :rtype: Channel
        """
        result = await self._request(f"radio/channels/livebuffer/{channel_id}")
        return Channel.from_dict(result["channel"])

    async def get_program(self, program_id: str) -> Program:
        """Get program.

        :param program_id:
        :rtype: Program
        """
        result = await self._request(f"radio/catalog/programs/{program_id}")
        return Program.from_dict(result)

    async def get_podcast(self, podcast_id: str) -> Podcast:
        """Get podcast.

        :param podcast_id:
        :rtype: Podcast
        """
        result = await self._request(f"radio/catalog/podcast/{podcast_id}")
        return Podcast.from_dict(result)

    async def get_podcasts(self, podcast_ids: list[str]) -> list[Podcast]:
        """Get podcasts.

        :param podcast_ids: List of podcast ids
        :type podcast_ids: list
        :rtype: list[Podcast]
        """
        results = await asyncio.gather(*[self.get_podcast(podcast_id) for podcast_id in podcast_ids])
        return list(results)

    async def get_podcast_season(self, podcast_id: str, season_id: str) -> Season:
        """Get podcast season.

        :param podcast_id:
        :param season_id:
        :rtype: Season
        """
        result = await self._request(f"radio/catalog/podcast/{podcast_id}/seasons/{season_id}")
        return Season.from_dict(result)

    async def get_podcast_episodes(self, podcast_id: str, season_id: str | None = None) -> list[Episode]:
        """Get podcast episodes.

        :param podcast_id:
        :param season_id:
        :rtype: list[Episode]
        """
        if season_id is not None:
            uri = f"radio/catalog/podcast/{podcast_id}/seasons/{season_id}/episodes"
        else:
            uri = f"radio/catalog/podcast/{podcast_id}/episodes"
        result = await self._request_paged_all(
            uri,
            items_key="_embedded.episodes",
        )
        return [Episode.from_dict(e) for e in result]

    async def get_all_podcasts(self) -> list[Series]:
        """Get all podcasts.

        :rtype: list[Series]
        """
        result = await self._request(
            "radio/search/categories/podcast",
            params={
                "take": 1000,
            },
        )
        return [Series.from_dict(s) for s in result["series"]]

    async def get_series(self, series_id: str) -> Podcast:
        """Get series.

        :param series_id:
        :rtype: :class:`nrk_psapi.models.catalog.Podcast`
        """
        result = await self._request(f"radio/catalog/series/{series_id}")
        return Podcast.from_dict(result)

    async def get_recommendations(
        self,
        item_id: str,
        context_id: RecommendationContext | None = None,
        limit: int | None = None,
    ) -> Recommendation:
        """Get recommendations.

        :param limit: Number of recommendations returned (max 25). Default is set to 12.
        :param context_id: Which context (front page, series page, etc.) the user is in.
        :param item_id: A id of a series/program/episode/season etc.
        :rtype: Recommendation
        """

        result = await self._request(
            f"radio/recommendations/{item_id}",
            params={
                "list": context_id,
                "maxNumber": limit,
            },
        )
        return Recommendation.from_dict(result)

    async def browse(
        self,
        letter: SingleLetter,
        per_page: int = 50,
        page: int = 1,
    ) -> PodcastSearchResponse:
        """Browse podcasts by letter.

        :param letter: A single letter
        :param per_page: Number of items per page, defaults to 50
        :type per_page: int, optional
        :param page: Page number, defaults to 1
        :type page: int, optional
        :rtype: PodcastSearchResponse
        """
        result = await self._request(
            "radio/search/categories/alt-innhold",
            params={
                "letter": letter,
                "take": per_page,
                "skip": (page - 1) * per_page,
                "page": page,
            },
        )
        return PodcastSearchResponse.from_dict(result)

    async def search(
        self,
        query: str,
        per_page: int = 50,
        page: int = 1,
        search_type: SearchResultType | SearchResultStrType | None = None,
    ) -> SearchResponse:
        """Search anything.

        :param query: Search query
        :param per_page: Number of items per page, defaults to 50
        :type per_page: int, optional
        :param page: Page number, defaults to 1
        :type page: int, optional
        :param search_type: Search type, one of :class:`SearchResultType`. Defaults to all.
        :type search_type: SearchResultType, optional
        :rtype: SearchResponse
        """
        result = await self._request(
            "radio/search/search",
            params={
                "q": query,
                "take": per_page,
                "skip": (page - 1) * per_page,
                "page": page,
                "type": str(search_type) if search_type else None,
            },
        )
        return SearchResponse.from_dict(result)

    async def search_suggest(self, query: str) -> list[str]:
        """Search autocomplete/auto-suggest.

        :param query: Search query
        :rtype: list[str]
        """
        return await self._request("/radio/search/search/suggest", params={"q": query})

    async def radio_pages(self) -> Pages:
        """Get radio pages.

        :rtype: Pages
        """
        result = await self._request("radio/pages")
        return Pages.from_dict(result)

    async def radio_page(self, page_id: str, section_id: str | None = None) -> Page | Included | None:
        """Get radio page.

        :param page_id: Name of the page, e.g. 'discover'
        :param section_id: Web friendly title of the section, e.g. 'krim-fra-virkeligheten'
        :type section_id: str, optional
        :rtype: Page
        """
        result = await self._request(f"radio/pages/{page_id}")
        page = Page.from_dict(result)
        if section_id is None:
            return page

        for section in page.sections:
            if isinstance(section, IncludedSection) and section.included.section_id == section_id:
                return section.included
        return None

    async def curated_podcasts(self) -> Curated:
        """Get curated podcasts.
        This is a wrapper around :meth:`radio_page`, with the section_id set to "podcast" and
        some logic to make it easier to use for accessing curated podcasts.

        :rtype: Curated
        """
        page = await self.radio_page(page_id="podcast")
        sections = []
        for section in page.sections:
            if isinstance(section, IncludedSection):
                podcasts = [
                    CuratedPodcast(
                        id=plug.id,
                        title=plug.title,
                        subtitle=plug.tagline,
                        image=plug.podcast.image_url,
                        number_of_episodes=plug.podcast.number_of_episodes,
                    )
                    for plug in section.included.plugs
                    if isinstance(plug, PodcastPlug)
                ]
                if len(podcasts) > 1:
                    sections.append(
                        CuratedSection(
                            id=sanitize_string(section.included.title),
                            title=section.included.title,
                            podcasts=podcasts,
                        )
                    )
        return Curated(sections=sections)

    async def fetch_file_info(self, url: URL | str):
        """Proxies call to `utils.fetch_file_info`, passing on self.session."""
        return await fetch_file_info(url, self.session)

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self):
        """Async enter."""
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit."""
        await self.close()
