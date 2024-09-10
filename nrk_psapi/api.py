"""nrk-psapi."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
import json
import socket
from typing import Self

from aiohttp.client import ClientError, ClientSession
from aiohttp.hdrs import METH_GET
import async_timeout
import backoff
from yarl import URL

from .const import LOGGER as _LOGGER, PSAPI_BASE_URL
from .exceptions import (
    NrkPsApiConnectionError,
    NrkPsApiConnectionTimeoutError,
    NrkPsApiError,
    NrkPsApiRateLimitError,
)
from .models.catalog import (
    Episode,
    Podcast,
    PodcastSeries,
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
    IncludedSection,
    Page,
    Pages,
    PodcastPlug,
)
from .models.playback import PodcastManifest
from .models.recommendations import Recommendation
from .models.search import (
    PodcastSearchResponse,
    SearchResponse,
    SearchResultStrType,
    SearchResultType,
    SingleLetter,
)
from .utils import get_nested_items, sanitize_string


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

    @backoff.on_exception(
        backoff.expo, NrkPsApiConnectionError, max_tries=5, logger=None
    )
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
            kwargs.update(params={k:v for k,v in params.items() if v is not None})

        try:
            async with async_timeout.timeout(self.request_timeout):
                response = await self.session.request(
                    method,
                    url,
                    **kwargs,
                    headers=headers,
                )
        except asyncio.TimeoutError as exception:
            raise NrkPsApiConnectionTimeoutError(
                "Timeout occurred while connecting to the PodMe API"
            ) from exception
        except (ClientError, socket.gaierror) as exception:
            raise NrkPsApiConnectionError(
                "Error occurred while communicating with the PodMe API"
            ) from exception

        content_type = response.headers.get("Content-Type", "")
        # Error handling
        if (response.status // 100) in [4, 5]:
            contents = await response.read()
            response.close()

            if response.status == HTTPStatus.TOO_MANY_REQUESTS:
                raise NrkPsApiRateLimitError(
                    "Rate limit error has occurred with the PodMe API"
                )

            if content_type == "application/json":
                raise NrkPsApiError(response.status, json.loads(contents.decode("utf8")))
            raise NrkPsApiError(response.status, {"message": contents.decode("utf8")})

        # Handle empty response
        if response.status == HTTPStatus.NO_CONTENT:
            _LOGGER.warning("Request to <%s> resulted in status 204. Your dataset could be out of date.", url)
            return None

        if "application/json" in content_type:
            result = await response.json()
            _LOGGER.debug("Response: %s", str(result))
            return result
        result = await response.text()
        _LOGGER.debug("Response: %s", str(result))
        return result

    async def ipcheck(self) -> IpCheck:
        """Check if IP is blocked.

        :rtype: IpCheck
        """
        result = await self._request("ipcheck")
        return IpCheck.from_dict(result["data"])

    async def get_playback_manifest(self, episode_id: str) -> PodcastManifest:
        """Get the manifest for an episode.

        :param episode_id:
        :rtype: PodcastManifest
        """
        result = await self._request(f"playback/manifest/{episode_id}")
        return PodcastManifest.from_dict(result)

    async def get_playback_metadata(self, episode_id: str) -> PodcastMetadata:
        """Get the metadata for an episode.

        :param episode_id:
        :rtype: PodcastMetadata
        """
        result = await self._request(f"playback/metadata/podcast/{episode_id}")
        return PodcastMetadata.from_dict(result)

    async def get_episode(self, podcast_id: str, episode_id: str) -> Episode:
        """Get episode.

        :param podcast_id:
        :param episode_id:
        :rtype: Episode
        """
        result = await self._request(f"radio/catalog/podcast/{podcast_id}/episodes/{episode_id}")
        return Episode.from_dict(result)

    async def get_series(self, series_id: str) -> PodcastSeries:
        """Get series.

        :param series_id:
        :rtype: :class:`nrk_psapi.models.catalog.PodcastSeries`
        """
        result = await self._request(f"radio/catalog/series/{series_id}")
        return PodcastSeries.from_dict(result)

    async def get_series_type(self, series_id: str) -> SeriesType:
        """Get series type.

        :param series_id:
        :rtype: SeriesType
        """
        result = await self._request(f"radio/catalog/series/{series_id}/type")
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
        result = await self._request(f"radio/catalog/program/{program_id}")
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
            }
        )
        return [Series.from_dict(s) for s in result["series"]]

    async def get_recommendations(self, item_id: str) -> Recommendation:
        """Get recommendations.

        :param item_id: A id of a series/program/episode/season etc.
        :rtype: Recommendation
        """
        result = await self._request(f"radio/recommendations/{item_id}")
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
            })
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
            })
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

    async def radio_page(self, page_id: str, section_id: str | None = None) -> Page:
        """Get radio page.

        :param page_id: Page id
        :param section_id: Section id, will return all sections if not provided
        :type section_id: str, optional
        :rtype: Page
        """
        uri = f"radio/pages/{page_id}"
        if section_id:
            uri += f"/{section_id}"
        result = await self._request(uri)
        return Page.from_dict(result)

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
                    sections.append(CuratedSection(
                        id=sanitize_string(section.included.title),
                        title=section.included.title,
                        podcasts=podcasts,
                    ))
        return Curated(sections=sections)

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> Self:
        """Async enter."""
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit."""
        await self.close()
