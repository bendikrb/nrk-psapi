"""nrk-psapi models."""

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING

from .catalog import (
    Availability,
    Contributor,
    Episode,
    EpisodeContext,
    EpisodeType,
    Image,
    IndexPoint,
    Link,
    Podcast,
    PodcastSequential,
    PodcastSeries,
    PodcastStandard,
    PodcastType,
    PodcastUmbrella,
    Program,
    ProgramInformation,
    ProgramInformationDetails,
    Season,
    SeasonBase,
    SeasonDisplayType,
    SeasonEmbedded,
    Series,
    SeriesType,
    Titles,
    UsageRights,
)
from .channels import Channel, ChannelEntry, ChannelImage, ChannelType, DistrictChannel
from .common import IpCheck
from .metadata import (
    Manifest,
    PodcastEpisodeMetadata,
    PodcastMetadata,
    PodcastMetadataEmbedded,
    Preplay,
)
from .pages import (
    ChannelPlug,
    Curated,
    CuratedPodcast,
    CuratedSection,
    EpisodePlug,
    Included,
    IncludedSection,
    LinkPlug,
    Page,
    PageListItem,
    PagePlug,
    Pages,
    PlaceholderSection,
    Plug,
    PluggedChannel,
    PluggedEpisode,
    PluggedPodcast,
    PluggedPodcastEpisode,
    PluggedPodcastSeason,
    PluggedSeries,
    PluggedStandaloneProgram,
    PlugType,
    PodcastEpisodePlug,
    PodcastPlug,
    PodcastSeasonPlug,
    Section,
    SeriesPlug,
    StandaloneProgramPlug,
)
from .playback import (
    AvailabilityDetailed,
    Playable,
    PodcastManifest,
)
from .recommendations import Recommendation
from .search import (
    CategoriesResponse,
    LetterListItem,
    PodcastSearchResponse,
    SearchedSeries,
    SearchResponse,
    SearchResponseResultCategory,
    SearchResponseResultChannel,
    SearchResponseResultCustomSeason,
    SearchResponseResultCustomSeasonEpisode,
    SearchResponseResultEpisode,
    SearchResponseResultPodcast,
    SearchResponseResultSeries,
    SearchResponseResultSeriesEpisode,
    SearchResultType,
    SeriesListItem,
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
def get_operation(path: str) -> Operation | None:  # pragma: no cover
    for operation in OPERATIONS.values():
        if operation["path"] == path:
            return operation
    return None


__all__ = [
    "Availability",
    "AvailabilityDetailed",
    "CategoriesResponse",
    "Channel",
    "ChannelEntry",
    "ChannelImage",
    "ChannelPlug",
    "ChannelType",
    "Contributor",
    "Curated",
    "Curated",
    "CuratedPodcast",
    "CuratedSection",
    "DistrictChannel",
    "Episode",
    "EpisodePlug",
    "EpisodeType",
    "get_operation",
    "Image",
    "Included",
    "IncludedSection",
    "IndexPoint",
    "IpCheck",
    "LetterListItem",
    "Link",
    "LinkPlug",
    "Page",
    "PageListItem",
    "PagePlug",
    "Pages",
    "PlaceholderSection",
    "Plug",
    "PlugType",
    "Podcast",
    "PodcastEpisodePlug",
    "PodcastManifest",
    "PodcastMetadata",
    "PodcastPlug",
    "PodcastSearchResponse",
    "PodcastSeasonPlug",
    "PodcastSequential",
    "PodcastSeries",
    "PodcastStandard",
    "PodcastType",
    "PodcastUmbrella",
    "Program",
    "ProgramInformation",
    "ProgramInformationDetails",
    "Playable",
    "Recommendation",
    "SearchResponse",
    "SearchResponseResultEpisode",
    "SearchResponseResultPodcast",
    "SearchResponseResultCategory",
    "SearchResponseResultChannel",
    "SearchResponseResultCustomSeason",
    "SearchResponseResultCustomSeasonEpisode",
    "SearchResponseResultSeries",
    "SearchResponseResultSeriesEpisode",
    "SearchResultType",
    "SearchedSeries",
    "Season",
    "SeasonBase",
    "SeasonDisplayType",
    "SeasonEmbedded",
    "Section",
    "Series",
    "SeriesListItem",
    "SeriesPlug",
    "SeriesType",
    "StandaloneProgramPlug",
    "Titles",
    "UsageRights",
    "PluggedChannel",
    "PluggedEpisode",
    "PluggedPodcast",
    "PluggedPodcastEpisode",
    "PluggedPodcastSeason",
    "PluggedSeries",
    "PluggedStandaloneProgram",
    "Manifest",
    "PodcastEpisodeMetadata",
    "PodcastMetadataEmbedded",
    "Preplay",
]
