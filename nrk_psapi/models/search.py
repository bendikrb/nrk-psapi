from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime  # noqa: TCH003
from typing import Literal

from mashumaro import field_options
from mashumaro.config import BaseConfig
from mashumaro.types import Discriminator

from .catalog import Image, Link
from .common import BaseDataClassORJSONMixin, StrEnum

SingleLetter = Literal[
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "Æ",
    "Ø",
    "Å",
    "#",
]


class SearchResultType(StrEnum):
    """The different types of search results that can be returned."""

    CATEGORY = "category"
    CHANNEL = "channel"
    PODCAST = "podcast"
    PODCAST_EPISODE = "podcastEpisode"
    SERIES = "series"
    SERIES_EPISODE = "seriesEpisode"
    CUSTOM_SEASON = "customSeason"
    CUSTOM_SEASON_EPISODE = "customSeasonEpisode"
    SINGLE_PROGRAM = "singleProgram"


SearchResultStrType = Literal[
    "category",
    "channel",
    "podcast",
    "podcastEpisode",
    "series",
    "seriesEpisode",
    "customSeason",
    "customSeasonEpisode",
    "singleProgram",
]


@dataclass
class SearchResultLink(BaseDataClassORJSONMixin):
    """Represents a link in the API search response."""

    next: str | None = None
    prev: str | None = None


@dataclass
class Links(BaseDataClassORJSONMixin):
    """Represents the _links object in the API response."""

    next_letter: Link | None = field(default=None, metadata=field_options(alias="nextLetter"))
    next_page: Link | None = field(default=None, metadata=field_options(alias="nextPage"))
    prev_letter: Link | None = field(default=None, metadata=field_options(alias="prevLetter"))
    prev_page: Link | None = field(default=None, metadata=field_options(alias="prevPage"))
    custom_season: Link | None = field(default=None, metadata=field_options(alias="customSeason"))
    single_program: Link | None = field(default=None, metadata=field_options(alias="singleProgram"))
    next: Link | None = None
    prev: Link | None = None
    podcast: Link | None = None
    series: Link | None = None


@dataclass
class SeriesListItemLinks(BaseDataClassORJSONMixin):
    series: Link | None = None
    podcast: Link | None = None
    custom_season: Link | None = None
    single_program: Link | None = None


@dataclass
class SeriesListItem(BaseDataClassORJSONMixin):
    _links: SeriesListItemLinks
    id: str
    type: Literal[
        SearchResultType.SERIES,
        SearchResultType.PODCAST,
        SearchResultType.SINGLE_PROGRAM,
        SearchResultType.CUSTOM_SEASON,
    ]
    title: str
    initial_character: str
    images: list[Image]
    series_id: str | None = None
    season_id: str | None = None


@dataclass
class LetterListItem(BaseDataClassORJSONMixin):
    letter: str
    count: int
    link: str


@dataclass
class CategoriesLinks(BaseDataClassORJSONMixin):
    next_page: Link | None = None
    prev_page: Link | None = None
    next_letter: Link | None = None
    prev_letter: Link | None = None


@dataclass
class CategoriesResponse(BaseDataClassORJSONMixin):
    _links: CategoriesLinks
    letters: list[LetterListItem]
    title: str
    series: list[SeriesListItem]
    total_count: int


@dataclass
class Letter(BaseDataClassORJSONMixin):
    """Represents a letter object in the letters array."""

    letter: SingleLetter
    count: int
    link: str


#
# @dataclass
# class Image(BaseDataClassORJSONMixin):
#     """Represents an image object in the images or squareImages arrays."""
#
#     uri: str
#     width: int


@dataclass
class Highlight(BaseDataClassORJSONMixin):
    """Represents a highlight object in the highlights array."""

    field: str
    text: str


@dataclass
class SearchedSeries(BaseDataClassORJSONMixin):
    """Represents a series object in the series array."""

    id: str
    series_id: str = field(metadata=field_options(alias="seriesId"))
    title: str
    type: SearchResultType
    initial_character: str = field(metadata=field_options(alias="initialCharacter"))
    images: list[Image]
    square_images: list[Image] = field(metadata=field_options(alias="squareImages"))
    _links: Links
    season_id: str | None = field(default=None, metadata=field_options(alias="seasonId"))


@dataclass
class PodcastSearchResponse(BaseDataClassORJSONMixin):
    """Represents the main response object from the podcast search API."""

    letters: list[Letter]
    title: str
    series: list[SearchedSeries]
    total_count: int = field(metadata=field_options(alias="totalCount"))
    _links: Links | None = None


@dataclass
class SearchResponseCounts(BaseDataClassORJSONMixin):
    """Represents the counts object in the main response object from the podcast search API."""

    all: int
    series: int
    episodes: int
    contributors: int
    contents: int
    categories: int
    channels: int


@dataclass
class SearchResponseResult(BaseDataClassORJSONMixin):
    """Represents the result object in the results array in the main response object from the podcast search API."""

    id: str
    type: SearchResultType
    images: list[Image]
    highlights: list[Highlight]

    class Config(BaseConfig):
        discriminator = Discriminator(
            field="type",
            include_subtypes=True,
        )


@dataclass
class SearchResponseResultCategory(SearchResponseResult):
    """Represents a category object in the results array in the main response object from the podcast search API."""

    type = SearchResultType.CATEGORY
    title: str


@dataclass
class SearchResponseResultChannel(SearchResponseResult):
    """Represents a channel object in the results array in the main response object from the podcast search API."""

    type = SearchResultType.CHANNEL
    title: str
    priority: float


@dataclass
class SearchResponseResultSeries(SearchResponseResult):
    """Represents a series object in the results array in the main response object from the podcast search API."""

    type = SearchResultType.SERIES
    title: str
    description: str
    series_id: str = field(metadata=field_options(alias="seriesId"))
    square_images: list[Image] = field(metadata=field_options(alias="images_1_1"))
    score: float


@dataclass
class SearchResponseResultCustomSeason(SearchResponseResult):
    """Represents a custom season object in the results array in the main response object from the podcast search API."""

    type = SearchResultType.CUSTOM_SEASON
    title: str
    description: str
    series_id: str = field(metadata=field_options(alias="seriesId"))
    season_id: str = field(metadata=field_options(alias="seasonId"))
    square_images: list[Image] = field(metadata=field_options(alias="images_1_1"))
    score: float


@dataclass
class SearchResponseResultPodcast(SearchResponseResult):
    """Represents a podcast object in the results array in the main response object from the podcast search API."""

    type = SearchResultType.PODCAST
    title: str
    description: str
    series_id: str = field(metadata=field_options(alias="seriesId"))
    square_images: list[Image] = field(metadata=field_options(alias="images_1_1"))
    score: float


@dataclass
class SearchResponseResultEpisode(SearchResponseResult):
    """Represents an episode object in the results array in the main response object from the podcast search API."""

    type = SearchResultType.PODCAST_EPISODE
    title: str
    episode_id: str = field(metadata=field_options(alias="episodeId"))
    series_id: str = field(metadata=field_options(alias="seriesId"))
    series_title: str = field(metadata=field_options(alias="seriesTitle"))
    date: datetime
    square_images: list[Image] = field(metadata=field_options(alias="images_1_1"))
    season_id: str | None = field(default=None, metadata=field_options(alias="seasonId"))


@dataclass
class SearchResponseResultCustomSeasonEpisode(SearchResponseResult):
    """Represents a custom season episode object in the results array in the main response object from the podcast search API."""

    type = SearchResultType.CUSTOM_SEASON_EPISODE
    title: str
    episode_id: str = field(metadata=field_options(alias="episodeId"))
    series_id: str = field(metadata=field_options(alias="seriesId"))
    series_title: str = field(metadata=field_options(alias="seriesTitle"))
    date: datetime
    square_images: list[Image] = field(metadata=field_options(alias="images_1_1"))
    season_id: str | None = field(default=None, metadata=field_options(alias="seasonId"))


@dataclass
class SearchResponseResultSeriesEpisode(SearchResponseResultEpisode):
    type = SearchResultType.SERIES_EPISODE


@dataclass
class SearchResponseResultsResult(BaseDataClassORJSONMixin):
    """Represents the result object in the results array in the main response object from the podcast search API."""

    results: list[SearchResponseResult]
    links: SearchResultLink | None = None


@dataclass
class SearchResponseResults(BaseDataClassORJSONMixin):
    """Represents the results object in the main response object from the podcast search API."""

    channels: SearchResponseResultsResult
    categories: SearchResponseResultsResult
    series: SearchResponseResultsResult
    episodes: SearchResponseResultsResult
    contents: SearchResponseResultsResult
    contributors: SearchResponseResultsResult


@dataclass
class SearchResponse(BaseDataClassORJSONMixin):
    """Represents the main response object from the podcast search API."""

    count: int
    take_count: SearchResponseCounts = field(metadata=field_options(alias="takeCount"))
    total_count: SearchResponseCounts = field(metadata=field_options(alias="totalCount"))
    results: SearchResponseResults
    is_suggest_result: bool = field(metadata=field_options(alias="isSuggestResult"))
