from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from mashumaro import field_options

from .common import BaseDataClassORJSONMixin

SingleLetter = Literal[
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
    'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'Æ', 'Ø', 'Å', '#',
]


@dataclass
class Link(BaseDataClassORJSONMixin):
    """Represents a link in the API response."""

    href: str


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
    podcast: Link | None = None


@dataclass
class Letter(BaseDataClassORJSONMixin):
    """Represents a letter object in the letters array."""

    letter: SingleLetter
    count: int
    link: str


@dataclass
class Image(BaseDataClassORJSONMixin):
    """Represents an image object in the images or squareImages arrays."""

    uri: str
    width: int


@dataclass
class Series(BaseDataClassORJSONMixin):
    """Represents a series object in the series array."""

    id: str
    series_id: str = field(metadata=field_options(alias="seriesId"))
    title: str
    type: str
    initial_character: str = field(metadata=field_options(alias="initialCharacter"))
    images: list[Image]
    square_images: list[Image] = field(metadata=field_options(alias="squareImages"))
    _links: Links
    season_id: str | None = field(default=None, metadata=field_options(alias="seasonId"))


@dataclass
class PodcastSearchResponse(BaseDataClassORJSONMixin):
    """Represents the main response object from the podcast search API."""

    _links: Links
    letters: list[Letter]
    title: str
    series: list[Series]
    total_count: int = field(metadata=field_options(alias="totalCount"))


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
class SearchResponseResultsResult(BaseDataClassORJSONMixin):
    """Represents the result object in the results array in the main response object from the podcast search API."""

    results: list[dict]
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
    take_count: SearchResponseCounts
    total_count: SearchResponseCounts
    results: SearchResponseResults
