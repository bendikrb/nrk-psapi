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

from .caching import cache, disable_cache
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
    CategoriesResponse,
    SearchResponse,
    SearchResultStrType,
    SearchResultType,
    SeriesListItem,
    SingleLetter,
)
from .utils import (
    fetch_file_info,
    get_nested_items,
    sanitize_string,
)


@dataclass
class NrkPodcastAPI:
    """NrkPodcastAPI.

    Args:
        user_agent(str, optional): User agent string
        enable_cache(bool, optional): Enable caching, defaults to True
        request_timeout(int, optional): Request timeout in seconds, defaults to 15
        session(ClientSession, optional): Optional web session to use for requests

    """

    user_agent: str | None = None
    enable_cache: bool = True

    request_timeout: int = 15
    session: ClientSession | None = None

    _close_session: bool = False

    def __post_init__(self):
        if not self.enable_cache:
            disable_cache()
            _LOGGER.debug("Cache disabled")

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
        page_size: int = 50,
        **kwargs,
    ) -> list:
        """Make a paged request."""
        results = []
        page = 1

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
        headers = kwargs.get("headers")
        headers = self.request_header if headers is None else dict(headers)

        params = kwargs.get("params")
        if params is not None:
            kwargs.update(params={k: v for k, v in params.items() if v is not None})

        if self.session is None:
            self.session = ClientSession()
            _LOGGER.debug("New session created.")
            self._close_session = True

        _LOGGER.debug(
            "Executing %s API request to %s.",
            method,
            url.with_query(kwargs.get("params")),
        )

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
        """Check if IP is blocked."""
        result = await self._request("ipcheck")
        return IpCheck.from_dict(result["data"])

    @cache(ignore=(0,))
    async def get_playback_manifest(
        self,
        item_id: str,
        *,
        podcast=False,
        program=False,
        channel=False,
    ) -> PodcastManifest:
        """Get the manifest for an episode/program/channel.

        Args:
            item_id(str): Media id
            channel(bool, optional): Media is a channel. Defaults to False.
            program(bool, optional): Media is a program. Defaults to False.
            podcast(bool, optional): Media is a podcast. Defaults to False.

        Returns:
            PodcastManifest

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

    @cache(ignore=(0,))
    async def get_playback_metadata(
        self,
        item_id: str,
        *,
        podcast=False,
        program=False,
        channel=False,
    ) -> PodcastMetadata:
        """Get the metadata for an episode/program/channel.

        Args:
            item_id(str, optional): Media id
            channel(bool, optional): Media is a channel. Defaults to False.
            program(bool, optional): Media is a program. Defaults to False.
            podcast(bool, optional): Media is a podcast. Defaults to False.

        Returns:
            PodcastMetadata

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

    @cache(ignore=(0,))
    async def get_episode(self, podcast_id: str, episode_id: str) -> Episode:
        """Get episode.

        Args:
            podcast_id(str): Podcast ID.
            episode_id(str): Episode ID.

        Returns:
            Episode

        """
        result = await self._request(f"radio/catalog/podcast/{podcast_id}/episodes/{episode_id}")
        return Episode.from_dict(result)

    @cache(ignore=(0,))
    async def get_series_type(self, series_id: str) -> SeriesType:
        """Get series type.

        Args:
            series_id(str): Series ID.

        Returns:
            SeriesType

        """
        result = await self._request(f"radio/catalog/series/{series_id}/type")
        return SeriesType.from_str(result["seriesType"])

    @cache(ignore=(0,))
    async def get_podcast_type(self, podcast_id: str) -> SeriesType:
        """Get podcast type.

        Args:
            podcast_id(str): Podcast ID.

        Returns:
            SeriesType

        """
        result = await self._request(f"radio/catalog/podcast/{podcast_id}/type")
        return SeriesType.from_str(result["seriesType"])

    @cache(ignore=(0,))
    async def get_series_season(self, series_id: str, season_id: str) -> Season:
        """Get series season.

        Args:
            series_id(str): Series ID.
            season_id(str): Season ID.

        Returns:
            Season

        """
        result = await self._request(f"radio/catalog/series/{series_id}/seasons/{season_id}")
        return Season.from_dict(result)

    @cache(ignore=(0,))
    async def get_series_episodes(
        self,
        series_id: str,
        season_id: str | None = None,
        *,
        page_size: int | None = None,
        page: int = 1,
    ) -> list[Episode]:
        """Get series episodes.

        Args:
            series_id(str): Series ID.
            season_id(str, optional): Season ID.
            page_size(int, optional): Number of episodes to return (defaults to all)
            page(int, optional): Page number

        Returns:
            list[Episode]

        """
        if season_id is not None:
            uri = f"radio/catalog/series/{series_id}/seasons/{season_id}/episodes"
        else:
            uri = f"radio/catalog/series/{series_id}/episodes"

        if page_size is not None:
            results = await self._request_paged(
                uri,
                page_size=page_size,
                page=page,
            )
            result = results.get("_embedded", {}).get("episodes", [])
        else:
            result = await self._request_paged_all(
                uri,
                items_key="_embedded.episodes",
            )
        return [Episode.from_dict(e) for e in result]

    @cache(ignore=(0,))
    async def get_live_channel(self, channel_id: str) -> Channel:
        """Get live channel.

        Args:
            channel_id(str): Channel ID.

        Returns:
            Channel

        """
        result = await self._request(f"radio/channels/livebuffer/{channel_id}")
        return Channel.from_dict(result["channel"])

    @cache(ignore=(0,))
    async def get_program(self, program_id: str) -> Program:
        """Get program.

        Args:
            program_id(str): Program ID.

        Returns:
            Program

        """
        result = await self._request(f"radio/catalog/programs/{program_id}")
        return Program.from_dict(result)

    @cache(ignore=(0,))
    async def get_podcast(self, podcast_id: str) -> Podcast:
        """Get podcast.

        Args:
            podcast_id(str): Podcast ID.

        Returns:
            Podcast

        """
        result = await self._request(f"radio/catalog/podcast/{podcast_id}")
        return Podcast.from_dict(result)

    # @cache(ignore=(0,))
    async def get_podcasts(self, podcast_ids: list[str]) -> list[Podcast]:
        """Get podcasts.

        Args:
            podcast_ids(list[str]): List of podcast ids.

        Returns:
            list[Podcast]

        """
        results = await asyncio.gather(*[self.get_podcast(podcast_id) for podcast_id in podcast_ids])
        return list(results)

    @cache(ignore=(0,))
    async def get_podcast_season(self, podcast_id: str, season_id: str) -> Season:
        """Get podcast season.

        Args:
            podcast_id(str): Podcast ID
            season_id(str): Season ID

        Returns:
            Season

        """
        result = await self._request(f"radio/catalog/podcast/{podcast_id}/seasons/{season_id}")
        return Season.from_dict(result)

    @cache(ignore=(0,))
    async def get_podcast_episodes(
        self,
        podcast_id: str,
        season_id: str | None = None,
        *,
        page_size: int | None = None,
        page: int = 1,
    ) -> list[Episode]:
        """Get podcast episodes.

        Args:
            podcast_id(str): Podcast ID
            season_id(str, optional): Season ID
            page_size(int, optional): Number of episodes to return (defaults to all)
            page(int, optional): Page number

        Returns:
            list[Episode]

        """
        if season_id is not None:
            uri = f"radio/catalog/podcast/{podcast_id}/seasons/{season_id}/episodes"
        else:
            uri = f"radio/catalog/podcast/{podcast_id}/episodes"

        if page_size is not None:
            results = await self._request_paged(
                uri,
                page_size=page_size,
                page=page,
            )
            result = results.get("_embedded", {}).get("episodes", [])
        else:
            result = await self._request_paged_all(
                uri,
                items_key="_embedded.episodes",
            )
        return [Episode.from_dict(e) for e in result]

    @cache(ignore=(0,))
    async def get_all_podcasts(self) -> list[SeriesListItem]:
        """Get all podcasts.

        Returns:
            list[Series]

        """
        result = await self._request(
            "radio/search/categories/podcast",
            params={
                "take": 1000,
            },
        )
        return [SeriesListItem.from_dict(s) for s in result["series"]]

    @cache(ignore=(0,))
    async def get_series(self, series_id: str) -> Podcast:
        """Get series.

        Args:
            series_id(str): Series ID.

        Returns:
            Podcast

        """
        result = await self._request(f"radio/catalog/series/{series_id}")
        return Podcast.from_dict(result)

    @cache(ignore=(0,))
    async def get_recommendations(
        self,
        item_id: str,
        context_id: RecommendationContext | None = None,
        limit: int | None = None,
    ) -> Recommendation:
        """Get recommendations.

        Args:
            item_id(str): A id of a series/program/episode/season etc.
            context_id(RecommendationContext, optional): Which context (front page, series page, etc.) the user is in.
            limit(int, optional): Number of recommendations returned (max 25). Defaults to 12.

        Returns:
            Recommendation

        """

        result = await self._request(
            f"radio/recommendations/{item_id}",
            params={
                "list": context_id,
                "maxNumber": limit,
            },
        )
        return Recommendation.from_dict(result)

    @cache(ignore=(0,))
    async def browse(
        self,
        letter: SingleLetter | None = None,
        category: str | None = None,
        per_page: int = 50,
        page: int = 1,
    ) -> CategoriesResponse:
        """Browse all series, podcast and umbrella seasons, optionally filtered by category.

        Alphabetical listing of all series, podcasts and umbrella seasons that are not excluded from search
        results in given category. Categories correspond to those in from `radio_pages`.
        For the category 'podcast', all podcasts are listed, also those excluded from search results.

        Args:
            category(str, optional): Category. Defaults to None, which will list all.
            letter(SingleLetter, optional): A single letter.
            per_page(int, optional): Number of items per page. Defaults to 50.
            page(int, optional): Page number. Defaults to 1.

        """

        if category is None:
            category = "alt-innhold"

        result = await self._request(
            f"radio/search/categories/{category}",
            params={
                "letter": letter,
                "take": per_page,
                "skip": (page - 1) * per_page,
                "page": page,
            },
        )
        return CategoriesResponse.from_dict(result)

    async def search(
        self,
        query: str,
        per_page: int = 50,
        page: int = 1,
        search_type: SearchResultType | SearchResultStrType | None = None,
    ) -> SearchResponse:
        """Search anything.

        Args:
            query(str): Search query.
            per_page(int, optional): Number of items per page. Defaults to 50.
            page(int, optional): Page number. Defaults to 1.
            search_type(SearchResultType, optional): Search type, one of :class:`~SearchResultType`. Defaults to all.

        Returns:
            SearchResponse

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

        Args:
            query(str): Search query

        Returns:
            list[str]: A list of suggestions.

        """
        return await self._request("/radio/search/search/suggest", params={"q": query})

    @cache(ignore=(0,))
    async def radio_pages(self) -> Pages:
        """Get radio pages.

        Returns:
            Pages

        """
        result = await self._request("radio/pages")
        return Pages.from_dict(result)

    @cache(ignore=(0,))
    async def radio_page(self, page_id: str, section_id: str | None = None) -> Page | Included | None:
        """Get radio page.

        Args:
            page_id(str): Name of the page, e.g. 'discover'.
            section_id(str, optional): Web friendly title of the section, e.g. 'krim-fra-virkeligheten'.

        Returns:
            Page

        """
        result = await self._request(f"radio/pages/{page_id}")
        page = Page.from_dict(result)
        if section_id is None:
            return page

        for section in page.sections:
            if isinstance(section, IncludedSection) and section.included.section_id == section_id:
                return section.included
        return None

    @cache(ignore=(0,))
    async def curated_podcasts(self) -> Curated:
        """Get curated podcasts.
        This is a wrapper around :meth:`radio_page`, with the section_id set to "podcast" and
        some logic to make it easier to use for accessing curated podcasts.

        Returns:
            Curated

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

    @cache(ignore=(0,))
    async def fetch_file_info(self, url: URL | str):
        """Proxies call to `utils.fetch_file_info`, passing on self.session.

        Args:
            url(URL | str): URL to fetch file info from.

        Returns:
            tuple[int, str]: content-length and content-type

        """
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
