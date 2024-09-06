"""nrk-psapi models."""
from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING

from .catalog import (
    Episode,
    EpisodeContext,
    Podcast,
    PodcastSeries,
    Season,
    SeriesType,
)
from .channels import Channel
from .pages import Curated, CuratedPodcast, CuratedSection
from .recommendations import Recommendation
from .search import (
    CategoriesResponse,
    SearchResponse,
)

if TYPE_CHECKING:
    from .common import Operation

# TODO(@bendikrb): Do another round here to align with the API.
OPERATIONS: dict[str, Operation] = {
    "Search": {
        "response_type": type["SearchResponse"],
        "path": "/radio/search/search",
    },
    "RadioSuggestSearch": {
        "response_type": list[str],
        "path": "/radio/search/search/suggest",
    },
    "RadioListAllForCategory": {
        "response_type": type["CategoriesResponse"],
        "path": "/radio/search/categories/{category}",
    },
    "GetEpisodeContext": {
        "response_type": type["EpisodeContext"],
        "path": "/radio/catalog/episode/context/{episodeId}",
    },
    "GetSeriesType": {
        "response_type": type["SeriesType"],
        "path": "/radio/catalog/series/{seriesId}/type",
    },
    "GetSeries": {
        "response_type": type["PodcastSeries"],
        "path": "/radio/catalog/series/{seriesId}",
    },
    "GetSeriesepisodes": {
        "response_type": list[type["Episode"]],
        "path": "/radio/catalog/series/{seriesId}/episodes",
    },
    "GetSeriesSeason": {
        "response_type": type["Season"],
        "path": "/radio/catalog/series/{seriesId}/seasons/{seasonId}",
    },
    "GetSeriesSeasonEpisodes": {
        "response_type": list[type["Episode"]],
        "path": "/radio/catalog/series/{seriesId}/seasons/{seasonId}/episodes",
    },
    "GetPodcast": {
        "response_type": type["Podcast"],
        "path": "/radio/catalog/podcast/{podcastId}",
    },
    "GetPodcastepisodes": {
        "response_type": list[type["Episode"]],
        "path": "/radio/catalog/podcast/{podcastId}/episodes",
    },
    "GetPodcastEpisode": {
        "response_type": type["Episode"],
        "path": "/radio/catalog/podcast/{podcastId}/episodes/{podcastEpisodeId}",
    },
    "GetPodcastSeason": {
        "response_type": type["Season"],
        "path": "/radio/catalog/podcast/{podcastId}/seasons/{seasonId}",
    },
    "GetPodcastSeasonEpisodes": {
        "response_type": list[type["Episode"]],
        "path": "/radio/catalog/podcast/{podcastId}/seasons/{seasonId}/episodes",
    },
}


@cache
def get_operation(path: str) -> Operation | None:
    for operation in OPERATIONS.values():
        if operation["path"] == path:
            return operation
    return None

__all__ = [
    "CategoriesResponse",
    "Channel",
    "Curated",
    "Curated",
    "CuratedPodcast",
    "CuratedSection",
    "Episode",
    "get_operation",
    "Podcast",
    "PodcastSeries",
    "Recommendation",
    "SearchResponse",
    "Season",
]
