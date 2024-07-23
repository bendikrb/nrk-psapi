from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from isodate import duration_isoformat, parse_duration
from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


@dataclass
class Date(DataClassORJSONMixin):
    """Represents a date with its value and display format."""

    date: datetime
    display_value: str = field(metadata=field_options(alias="displayValue"))


@dataclass
class GeoBlock(DataClassORJSONMixin):
    """Represents geographical blocking information."""

    is_geo_blocked: bool = field(metadata=field_options(alias="isGeoBlocked"))
    display_value: str = field(metadata=field_options(alias="displayValue"))


@dataclass
class UsageRights(DataClassORJSONMixin):
    """Contains information about usage rights and availability."""

    _from: Date = field(metadata=field_options(alias="from"))
    to: Date
    geo_block: GeoBlock = field(metadata=field_options(alias="geoBlock"))


@dataclass
class Availability(DataClassORJSONMixin):
    """Represents the availability status of an episode."""

    status: str
    has_label: bool = field(metadata=field_options(alias="hasLabel"))


@dataclass
class Category(DataClassORJSONMixin):
    """Represents a category with its ID and name."""

    id: str
    name: str | None = None
    display_value: str | None = field(default=None, metadata=field_options(alias="displayValue"))


@dataclass
class Titles(DataClassORJSONMixin):
    """Contains title information for an episode."""

    title: str
    subtitle: str


@dataclass
class Episode(DataClassORJSONMixin):
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
class EpisodesResponse(DataClassORJSONMixin):
    """Contains a list of embedded episodes."""

    _links: Links
    series_type: str = field(metadata=field_options(alias="seriesType"))
    episodes: list[Episode] = field(
        metadata=field_options(
            alias="_embedded",
            deserialize=lambda x: x["episodes"]["_embedded"]["episodes"],
        ))


@dataclass
class PodcastSeries(DataClassORJSONMixin):
    id: str
    titles: Titles
    category: Category
    image: list[Image]
    backdrop_image: list[Image] = field(metadata=field_options(alias="backdropImage"))
    poster_image: list[Image] = field(metadata=field_options(alias="posterImage"))
    square_image: list[Image] = field(metadata=field_options(alias="squareImage"))


@dataclass
class Podcast(DataClassORJSONMixin):
    """Represents the main structure of the API response."""

    _links: Links
    series_type: str = field(metadata=field_options(alias="seriesType"))
    type: str = field(metadata=field_options(alias="type"))
    season_display_type: str = field(metadata=field_options(alias="seasonDisplayType"))
    series: PodcastSeries

    episodes: list[Episode] = field(
        metadata=field_options(
            alias="_embedded",
            deserialize=lambda x: x["episodes"]["_embedded"]["episodes"],
        ))


@dataclass
class Link(DataClassORJSONMixin):
    """Represents a hyperlink in the API response."""

    href: str
    name: str | None = None
    title: str | None = None
    templated: bool | None = None


@dataclass
class Links(DataClassORJSONMixin):
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
class ProgramInformationDetails(DataClassORJSONMixin):
    """Contains program information details."""

    display_value: str = field(metadata=field_options(alias="displayValue"))
    accessibility_value: str = field(metadata=field_options(alias="accessibilityValue"))


@dataclass
class ProgramInformation(DataClassORJSONMixin):
    """Contains program information."""

    details: ProgramInformationDetails
    original_title: str = field(metadata=field_options(alias="originalTitle"))


@dataclass
class Contributor(DataClassORJSONMixin):
    """Represents a contributor to the episode."""

    role: str
    name: list[str]


@dataclass
class Image(DataClassORJSONMixin):
    """Represents an image with its URL and width."""

    url: str = field(metadata=field_options(alias="uri"))
    width: int | None = None
    pixel_width: int | None = field(default=None, metadata=field_options(alias="pixelWidth"))


@dataclass
class Duration(DataClassORJSONMixin):
    """Represents the duration of the episode in various formats."""

    seconds: int
    iso8601: str
    display_value: str = field(metadata=field_options(alias="displayValue"))


@dataclass
class IndexPoint(DataClassORJSONMixin):
    """Represents a point of interest within the episode."""

    title: str
    start_point: timedelta = field(metadata=field_options(
        alias="startPoint",
        deserialize=parse_duration,
        serialize=duration_isoformat,
    ))
    part_id: int | None = field(default=None, metadata=field_options(alias="partId"))


@dataclass
class Series(DataClassORJSONMixin):
    _links: Links
    id: str
    series_id: str = field(metadata=field_options(alias="seriesId"))
    title: str
    type: str
    images: list[Image]
    square_images: list[Image] = field(metadata=field_options(alias="squareImages"))
    season_id: str | None = field(default=None, metadata=field_options(alias="seasonId"))
