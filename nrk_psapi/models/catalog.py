from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta  # noqa: TCH003
from typing import Literal

from isodate import duration_isoformat, parse_duration
from mashumaro import field_options

from .common import BaseDataClassORJSONMixin


def deserialize_embedded(data, ret_type: Literal["episodes", "seasons"]) -> list[Episode | Season]:
    """Deserialize embedded episodes/seasons."""

    if ret_type == "seasons" and "seasons" in data:
        return [Season.from_dict(d) for d in data["seasons"]]
    if ret_type == "episodes" and "episodes" in data:
        return [Episode.from_dict(d) for d in data["episodes"]["_embedded"]["episodes"]]
    return []


@dataclass
class Date(BaseDataClassORJSONMixin):
    """Represents a date with its value and display format."""

    date: datetime
    display_value: str = field(metadata=field_options(alias="displayValue"))


@dataclass
class GeoBlock(BaseDataClassORJSONMixin):
    """Represents geographical blocking information."""

    is_geo_blocked: bool = field(metadata=field_options(alias="isGeoBlocked"))
    display_value: str = field(metadata=field_options(alias="displayValue"))


@dataclass
class UsageRights(BaseDataClassORJSONMixin):
    """Contains information about usage rights and availability."""

    _from: Date = field(metadata=field_options(alias="from"))
    to: Date
    geo_block: GeoBlock = field(metadata=field_options(alias="geoBlock"))


@dataclass
class Availability(BaseDataClassORJSONMixin):
    """Represents the availability status of an episode."""

    status: str
    has_label: bool = field(metadata=field_options(alias="hasLabel"))


@dataclass
class Category(BaseDataClassORJSONMixin):
    """Represents a category with its ID and name."""

    id: str
    name: str | None = None
    display_value: str | None = field(default=None, metadata=field_options(alias="displayValue"))


@dataclass
class Titles(BaseDataClassORJSONMixin):
    """Contains title information for an episode."""

    title: str
    subtitle: str | None = None


@dataclass
class Episode(BaseDataClassORJSONMixin):
    """Represents a podcast episode."""

    _links: Links
    id: str
    episode_id: str = field(metadata=field_options(alias="episodeId"))
    titles: Titles
    image: list[Image]
    square_image: list[Image] = field(metadata=field_options(alias="squareImage"))
    duration: timedelta = field(metadata=field_options(deserialize=parse_duration, serialize=duration_isoformat))
    date: datetime
    usage_rights: UsageRights = field(metadata=field_options(alias="usageRights"))
    availability: Availability
    category: Category
    original_title: str | None = field(default=None, metadata=field_options(alias="originalTitle"))
    badges: list | None = None
    duration_in_seconds: int | None = field(default=None, metadata=field_options(alias="durationInSeconds"))
    clip_id: str | None = field(default=None, metadata=field_options(alias="clipId"))


@dataclass
class Season(BaseDataClassORJSONMixin):
    """Represents a podcast season."""

    _links: Links
    id: str
    titles: Titles
    has_available_episodes: bool = field(metadata=field_options(alias="hasAvailableEpisodes"))
    episode_count: int = field(metadata=field_options(alias="episodeCount"))
    episodes: EpisodesResponse
    image: list[Image]
    square_image: list[Image] = field(metadata=field_options(alias="squareImage"))
    backdrop_image: list[Image] = field(metadata=field_options(alias="backdropImage"))


@dataclass
class EpisodesResponse(BaseDataClassORJSONMixin):
    """Contains a list of embedded episodes."""

    _links: Links
    episodes: list[Episode] = field(
        metadata=field_options(
            alias="_embedded",
            deserialize=lambda x: x["episodes"],
        ))
    series_type: str | None = field(default=None, metadata=field_options(alias="seriesType"))


@dataclass
class PodcastSeries(BaseDataClassORJSONMixin):
    id: str
    titles: Titles
    category: Category
    image: list[Image]
    backdrop_image: list[Image] = field(metadata=field_options(alias="backdropImage"))
    poster_image: list[Image] = field(metadata=field_options(alias="posterImage"))
    square_image: list[Image] = field(metadata=field_options(alias="squareImage"))


@dataclass
class Podcast(BaseDataClassORJSONMixin):
    """Represents the main structure of the API response."""

    _links: Links
    series_type: str = field(metadata=field_options(alias="seriesType"))
    type: str = field(metadata=field_options(alias="type"))
    season_display_type: str = field(metadata=field_options(alias="seasonDisplayType"))
    series: PodcastSeries

    episodes: list[Episode] = field(
        default_factory=list,
        metadata=field_options(
            alias="_embedded",
            deserialize=lambda x: deserialize_embedded(x, "episodes"),
        ))

    seasons: list[Season] = field(
        default_factory=list,
        metadata=field_options(
            alias="_embedded",
            deserialize=lambda x: deserialize_embedded(x, "seasons"),
        ))


@dataclass
class Link(BaseDataClassORJSONMixin):
    """Represents a hyperlink in the API response."""

    href: str
    name: str | None = None
    title: str | None = None
    templated: bool | None = None


@dataclass
class Links(BaseDataClassORJSONMixin):
    """Contains all the hyperlinks in the API response."""

    self: Link | None = None
    manifests: list[Link] | None = None
    next: Link | None = None
    next_links: list[Link] | None = field(default=None, metadata=field_options(alias="nextLinks"))
    playback: Link | None = None
    series: Link | None = None
    season: Link | None = None
    seasons: list[Link] | None = None
    custom_season: Link | None = field(default=None, metadata=field_options(alias="customSeason"))
    podcast: Link | None = None
    favourite: Link | None = None
    share: Link | None = None
    progress: Link | None = None
    progresses: list[Link] | None = None
    recommendations: Link | None = None
    extra_material: Link | None = field(default=None, metadata=field_options(alias="extraMaterial"))
    personalized_next: Link | None = field(default=None, metadata=field_options(alias="personalizedNext"))
    user_data: Link | None = field(default=None, metadata=field_options(alias="userData"))
    episodes: Link | None = None
    highlighted_episode: Link | None = field(default=None, metadata=field_options(alias="highlightedEpisode"))


@dataclass
class ProgramInformationDetails(BaseDataClassORJSONMixin):
    """Contains program information details."""

    display_value: str = field(metadata=field_options(alias="displayValue"))
    accessibility_value: str = field(metadata=field_options(alias="accessibilityValue"))


@dataclass
class ProgramInformation(BaseDataClassORJSONMixin):
    """Contains program information."""

    details: ProgramInformationDetails
    original_title: str = field(metadata=field_options(alias="originalTitle"))


@dataclass
class Contributor(BaseDataClassORJSONMixin):
    """Represents a contributor to the episode."""

    role: str
    name: list[str]


@dataclass
class Image(BaseDataClassORJSONMixin):
    """Represents an image with its URL and width."""

    url: str = field(metadata=field_options(alias="uri"))
    width: int | None = None
    pixel_width: int | None = field(default=None, metadata=field_options(alias="pixelWidth"))


@dataclass
class Duration(BaseDataClassORJSONMixin):
    """Represents the duration of the episode in various formats."""

    seconds: int
    iso8601: str
    display_value: str = field(metadata=field_options(alias="displayValue"))


@dataclass
class IndexPoint(BaseDataClassORJSONMixin):
    """Represents a point of interest within the episode."""

    title: str
    start_point: timedelta = field(metadata=field_options(
        alias="startPoint",
        deserialize=parse_duration,
        serialize=duration_isoformat,
    ))
    part_id: int | None = field(default=None, metadata=field_options(alias="partId"))


@dataclass
class Series(BaseDataClassORJSONMixin):
    _links: Links
    id: str
    series_id: str = field(metadata=field_options(alias="seriesId"))
    title: str
    type: str
    images: list[Image]
    square_images: list[Image] = field(metadata=field_options(alias="squareImages"))
    season_id: str | None = field(default=None, metadata=field_options(alias="seasonId"))
