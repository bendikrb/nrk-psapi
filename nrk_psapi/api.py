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
from .models.catalog import Episode, Podcast, Series
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
from .models.search import PodcastSearchResponse, SingleLetter
from .utils import get_nested_items, sanitize_string


@dataclass
class NrkPodcastAPI:

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

        try:
            with async_timeout.timeout(self.request_timeout):
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
        result = await self._request("ipcheck")
        return IpCheck.from_dict(result["data"])

    async def get_playback_manifest(self, episode_id: str) -> PodcastManifest:
        result = await self._request(f"playback/manifest/{episode_id}")
        return PodcastManifest.from_dict(result)

    async def get_playback_metadata(self, episode_id: str) -> PodcastMetadata:
        result = await self._request(f"playback/metadata/podcast/{episode_id}")
        return PodcastMetadata.from_dict(result)

    async def get_episode(self, podcast_id: str, episode_id: str) -> Episode:
        result = await self._request(f"radio/catalog/podcast/{podcast_id}/episodes/{episode_id}")
        return Episode.from_dict(result)

    async def get_podcast(self, podcast_id: str) -> Podcast:
        result = await self._request(f"radio/catalog/podcast/{podcast_id}")
        return Podcast.from_dict(result)

    async def get_podcasts(self, podcast_ids: list[str]) -> list[Podcast]:
        results: list[Podcast] = await asyncio.gather(*[self.get_podcast(podcast_id) for podcast_id in podcast_ids])
        return results

    async def get_podcast_episodes(self, podcast_id: str) -> list[Episode]:
        result = await self._request_paged_all(
            f"radio/catalog/podcast/{podcast_id}/episodes",
            items_key="_embedded.episodes",
        )
        return [Episode.from_dict(e) for e in result]

    async def get_all_podcasts(self) -> list[Series]:
        result = await self._request(
            "radio/search/categories/podcast",
            params={
                "take": 1000,
            }
        )
        return [Series.from_dict(s) for s in result["series"]]

    async def browse(self, letter: SingleLetter, take: int = 50, skip: int = 0) -> PodcastSearchResponse:
        result = await self._request(
            "radio/search/categories/alt-innhold",
            params={
                "letter": letter,
                "take": take,
                "skip": skip,
            })
        return PodcastSearchResponse.from_dict(result)

    async def search(self, query: str, take: int = 50, skip: int = 0) -> PodcastSearchResponse:
        result = await self._request(
            "radio/search/search",
            params={
                "q": query,
                "take": take,
                "skip": skip,
            })
        return PodcastSearchResponse.from_dict(result)

    async def radio_pages(self) -> Pages:
        result = await self._request("radio/pages")
        return Pages.from_dict(result)

    async def radio_page(self, page_id: str, section_id: str | None = None) -> Page:
        uri = f"radio/pages/{page_id}"
        if section_id:
            uri += f"/{section_id}"
        result = await self._request(uri)
        return Page.from_dict(result)

    async def curated_podcasts(self) -> Curated:
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
