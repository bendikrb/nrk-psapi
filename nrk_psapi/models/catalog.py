from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta  # noqa: TCH003
import re

from isodate import duration_isoformat, parse_duration
from mashumaro import field_options
from mashumaro.config import BaseConfig
from mashumaro.types import Discriminator

from .common import BaseDataClassORJSONMixin, StrEnum, T


class PodcastType(StrEnum):
    PODCAST = "podcast"
    CUSTOM_SEASON = "customSeason"
    SERIES = "series"


class EpisodeType(StrEnum):
    PODCAST_EPISODE = "podcast_episode"
    PROGRAM = "program"


class SeriesType(StrEnum):
    SEQUENTIAL = "sequential"
    NEWS = "news"
    STANDARD = "standard"
    UMBRELLA = "umbrella"


class SeasonDisplayType(StrEnum):
    MANUAL = "manual"
    NUMBER = "number"
    MONTH = "month"
    YEAR = "year"


@dataclass
class Date(BaseDataClassORJSONMixin):
    """Represents a date with its value and display format."""

    date: datetime
    display_value: str = field(metadata=field_options(alias="displayValue"))

    def __str__(self):
        return self.display_value


@dataclass
class GeoBlock(BaseDataClassORJSONMixin):
    """Represents geographical blocking information."""

    is_geo_blocked: bool = field(metadata=field_options(alias="isGeoBlocked"))
    display_value: str = field(metadata=field_options(alias="displayValue"))

    def __str__(self):
        return self.display_value


@dataclass
class UsageRights(BaseDataClassORJSONMixin):
    """Contains information about usage rights and availability."""

    _from: Date = field(metadata=field_options(alias="from"))
    to: Date
    geo_block: GeoBlock = field(metadata=field_options(alias="geoBlock"))

    def __str__(self):
        return f"{self._from} - {self.to} ({self.geo_block})"


@dataclass
class Availability(BaseDataClassORJSONMixin):
    """Represents the availability status of an episode."""

    status: str
    has_label: bool = field(metadata=field_options(alias="hasLabel"))

    def __str__(self):
        return self.status


@dataclass
class Category(BaseDataClassORJSONMixin):
    """Represents a category with its ID and name."""

    id: str
    name: str | None = None
    display_value: str | None = field(default=None, metadata=field_options(alias="displayValue"))

    def __str__(self):
        return self.display_value or self.id


@dataclass
class Titles(BaseDataClassORJSONMixin):
    """Contains title information."""

    title: str
    subtitle: str | None = None

    def __str__(self):
        return self.title


@dataclass
class DefaultTitles(BaseDataClassORJSONMixin):
    main_title: str = field(metadata=field_options(alias="mainTitle"))
    subtitle: str | None = field(default=None, metadata=field_options(alias="subtitle"))

    def __str__(self):
        title = self.main_title
        if self.subtitle:
            title += f" - {self.subtitle}"
        return title


@dataclass
class TemporalTitles(BaseDataClassORJSONMixin):
    titles: list[str]
    default_titles: DefaultTitles = field(metadata=field_options(alias="defaultTitles"))

    def __str__(self):
        if len(self.titles):
            return " - ".join(self.titles)
        return str(self.default_titles)


@dataclass
class EpisodeContext(BaseDataClassORJSONMixin):
    _links: Links
    type: PodcastType


@dataclass
class Episode(BaseDataClassORJSONMixin):
    """Represents a podcast episode."""

    _links: Links
    id: str
    type: EpisodeType
    episode_id: str = field(metadata=field_options(alias="episodeId"))
    titles: Titles
    duration: timedelta = field(
        metadata=field_options(deserialize=parse_duration, serialize=duration_isoformat)
    )
    date: datetime
    usage_rights: UsageRights = field(metadata=field_options(alias="usageRights"))
    availability: Availability
    program_information: ProgramInformation | None = field(
        default=None, metadata=field_options(alias="programInformation")
    )
    image: list[Image] | None = None
    square_image: list[Image] | None = field(default=None, metadata=field_options(alias="squareImage"))
    category: Category | None = None
    badges: list | None = None
    duration_in_seconds: int | None = field(default=None, metadata=field_options(alias="durationInSeconds"))
    clip_id: str | None = field(default=None, metadata=field_options(alias="clipId"))
    original_title: str | None = field(default=None, metadata=field_options(alias="originalTitle"))
    production_year: int | None = field(default=None, metadata=field_options(alias="productionYear"))
    index_points: list[IndexPoint] | None = field(default=None, metadata=field_options(alias="indexPoints"))
    contributors: list[Contributor] | None = None

    @classmethod
    def __pre_deserialize__(cls: type[T], d: T) -> T:
        self_href = d.get("_links", {}).get("self", {}).get("href")
        types = {
            EpisodeType.PODCAST_EPISODE: r"/radio/catalog/podcast/(.*)/episodes/(.*)",
            EpisodeType.PROGRAM: r"/radio/catalog/programs/(.*)",
        }
        for t, pattern in types.items():
            if re.match(pattern, self_href):
                d["type"] = t
                break

        if isinstance(d.get("duration"), Duration):
            d["duration"] = d["duration"].iso8601
        if isinstance(d.get("duration"), dict) and d["duration"].get("iso8601"):
            d["duration"] = d["duration"]["iso8601"]
        return d

    @classmethod
    def __post_deserialize__(cls: type[T], d: T) -> T:
        return d


@dataclass
class SeasonBase(BaseDataClassORJSONMixin):
    """Base class for a podcast season."""

    _links: Links
    titles: Titles
    has_available_episodes: bool = field(metadata=field_options(alias="hasAvailableEpisodes"))
    episode_count: int = field(metadata=field_options(alias="episodeCount"))
    image: list[Image]


@dataclass
class SeasonEmbedded(SeasonBase):
    """Represents an embedded podcast season."""

    id: str
    episodes: list[Episode] | None = field(
        default=None,
        metadata=field_options(
            deserialize=lambda x: [Episode.from_dict(d) for d in x["_embedded"]["episodes"]],
        ),
    )


@dataclass
class Season(SeasonBase):
    """Represents a podcast season."""

    series_type: SeriesType = field(metadata=field_options(alias="seriesType"))
    type: PodcastType = field(metadata=field_options(alias="type"))
    episodes: list[Episode] = field(
        metadata=field_options(
            alias="_embedded",
            deserialize=lambda x: [Episode.from_dict(d) for d in x["episodes"]["_embedded"]["episodes"]],
        )
    )
    name: str | None = None
    category: Category | None = None
    id: str | None = None
    series_id: str | None = None
    podcast_id: str | None = None
    square_image: list[Image] | None = field(default=None, metadata=field_options(alias="squareImage"))
    backdrop_image: list[Image] | None = field(default=None, metadata=field_options(alias="backdropImage"))

    @classmethod
    def __pre_deserialize__(cls: type[T], d: T) -> T:
        self_id = d.get("_links", {}).get("self", {}).get("href", "").split("/").pop()
        series_id = d.get("_links", {}).get("series", {}).get("name")
        podcast_id = d.get("_links", {}).get("podcast", {}).get("name")
        if series_id:
            d["series_id"] = series_id
        if podcast_id:
            d["podcast_id"] = podcast_id
        if not d.get("name") and self_id:
            d["name"] = self_id
        return d


@dataclass
class EpisodesResponse(BaseDataClassORJSONMixin):
    """Contains a list of embedded episodes."""

    _links: Links
    episodes: list[Episode] = field(
        metadata=field_options(
            alias="_embedded",
            deserialize=lambda x: x["episodes"],
        )
    )
    series_type: SeriesType | None = field(default=None, metadata=field_options(alias="seriesType"))


@dataclass
class PodcastSeries(BaseDataClassORJSONMixin):
    id: str
    title: str = field(init=False)
    titles: Titles
    category: Category
    image: list[Image]
    square_image: list[Image] | None = field(default=None, metadata=field_options(alias="squareImage"))
    backdrop_image: list[Image] | None = field(default=None, metadata=field_options(alias="backdropImage"))
    poster_image: list[Image] | None = field(default=None, metadata=field_options(alias="posterImage"))
    highlighted_episode: str | None = field(default=None, metadata=field_options(alias="highlightedEpisode"))
    next_episode: Date | None = field(default=None, metadata=field_options(alias="nextEpisode"))

    def __post_init__(self):
        self.title = self.titles.title


@dataclass
class Podcast(BaseDataClassORJSONMixin):
    """Represents the main structure of the API response."""

    _links: Links
    type: PodcastType = field(metadata=field_options(alias="type"))
    series_type: SeriesType = field(metadata=field_options(alias="seriesType"))
    season_display_type: SeasonDisplayType = field(metadata=field_options(alias="seasonDisplayType"))
    series: PodcastSeries

    class Config(BaseConfig):
        discriminator = Discriminator(
            field="seriesType",
            include_subtypes=True,
        )


@dataclass
class PodcastStandard(Podcast):
    seriesType = SeriesType.STANDARD  # noqa: N815
    episodes: list[Episode] = field(
        default_factory=list,
        metadata=field_options(
            alias="_embedded",
            deserialize=lambda x: [Episode.from_dict(d) for d in x["episodes"]["_embedded"]["episodes"]],
        ),
    )
    seasons: list[SeasonLink] = field(default_factory=list)

    @classmethod
    def __pre_deserialize__(cls: type[T], d: T) -> T:
        season_links = d.get("_links", {}).get("seasons", [])
        d["seasons"] = [{"id": d["name"], "title": d["title"]} for d in season_links]
        return d


@dataclass
class PodcastUmbrella(Podcast):
    seriesType = SeriesType.UMBRELLA  # noqa: N815
    seasons: list[SeasonEmbedded] = field(
        default_factory=list,
        metadata=field_options(
            alias="_embedded",
            deserialize=lambda x: [SeasonEmbedded.from_dict(d) for d in x["seasons"]],
        ),
    )


@dataclass
class PodcastSequential(Podcast):
    seriesType = SeriesType.SEQUENTIAL  # noqa: N815
    seasons: list[SeasonEmbedded] = field(
        default_factory=list,
        metadata=field_options(
            alias="_embedded",
            deserialize=lambda x: [SeasonEmbedded.from_dict(d) for d in x["seasons"]],
        ),
    )


@dataclass
class SeasonLink(BaseDataClassORJSONMixin):
    id: str
    title: str


@dataclass
class Link(BaseDataClassORJSONMixin):
    """Represents a hyperlink in the API response."""

    href: str
    name: str | None = None
    title: str | None = None
    templated: bool | None = None

    def __str__(self):
        return self.href


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

    def __str__(self):
        return self.display_value


@dataclass
class ProgramInformation(BaseDataClassORJSONMixin):
    """Contains program information."""

    details: ProgramInformationDetails
    original_title: str | None = field(default=None, metadata=field_options(alias="originalTitle"))

    def __str__(self):
        if self.original_title is None:
            return str(self.details)
        return f"{self.original_title} ({self.details})"


@dataclass
class Contributor(BaseDataClassORJSONMixin):
    """Represents a contributor to the episode."""

    role: str
    name: list[str]

    @classmethod
    def __pre_deserialize__(cls: type[T], d: T) -> T:
        name = d.get("name", [])
        if not isinstance(name, list):
            d["name"] = [name]
        return d


@dataclass
class WebImage(BaseDataClassORJSONMixin):
    """Wrapper around Image."""

    id: str
    web_images: list[Image] = field(metadata=field_options(alias="webImages"))


@dataclass
class Image(BaseDataClassORJSONMixin):
    """Represents an image with its URL and width."""

    url: str = field(metadata=field_options(alias="uri"))
    width: int | None = None
    pixel_width: int | None = field(default=None, metadata=field_options(alias="pixelWidth"))

    def __str__(self):
        return self.url


@dataclass
class Duration(BaseDataClassORJSONMixin):
    """Represents the duration of the episode in various formats."""

    seconds: int
    iso8601: timedelta = field(
        metadata=field_options(
            deserialize=parse_duration,
            serialize=duration_isoformat,
        )
    )
    display_value: str = field(metadata=field_options(alias="displayValue"))

    def __str__(self):
        return self.display_value


@dataclass
class IndexPoint(BaseDataClassORJSONMixin):
    """Represents a point of interest within the episode."""

    title: str
    start_point: timedelta = field(
        metadata=field_options(
            alias="startPoint",
            deserialize=parse_duration,
            serialize=duration_isoformat,
        )
    )
    description: str | None = None
    part_id: int | None = field(default=None, metadata=field_options(alias="partId"))
    mentioned: list[str] | None = None
    subject_list: list[str] | None = field(default=None, metadata=field_options(alias="subjectList"))
    contributors: list[Contributor] | None = None

    def __str__(self):
        return f"{self.start_point.total_seconds()}s: {self.title}"


@dataclass
class PlaylistItem(BaseDataClassORJSONMixin):
    """Represents a playlist item in the playlist."""

    title: str
    type: str
    description: str
    program_id: str = field(metadata=field_options(alias="programId"))
    channel_id: str = field(metadata=field_options(alias="channelId"))
    start_time: datetime = field(metadata=field_options(alias="startTime"))
    duration: timedelta = field(
        metadata=field_options(deserialize=parse_duration, serialize=duration_isoformat)
    )
    program_title: str = field(metadata=field_options(alias="programTitle"))
    start_point: timedelta = field(
        metadata=field_options(
            alias="startPoint",
            deserialize=parse_duration,
            serialize=duration_isoformat,
        )
    )

    class Config(BaseConfig):
        discriminator = Discriminator(
            field="type",
            include_subtypes=True,
        )


@dataclass
class PlaylistMusicItem(PlaylistItem):
    type = "Music"


@dataclass
class Series(BaseDataClassORJSONMixin):
    """Represents a series object."""

    _links: Links
    id: str
    series_id: str = field(metadata=field_options(alias="seriesId"))
    title: str
    type: PodcastType
    images: list[Image]
    square_images: list[Image] = field(metadata=field_options(alias="squareImages"))
    season_id: str | None = field(default=None, metadata=field_options(alias="seasonId"))


@dataclass
class Program(BaseDataClassORJSONMixin):
    """Represents a program object."""

    _links: Links
    id: str
    episode_id: str = field(metadata=field_options(alias="episodeId"))
    date: datetime
    program_information: ProgramInformation = field(metadata=field_options(alias="programInformation"))
    contributors: list[Contributor]
    image: list[Image]
    temporal_titles: TemporalTitles = field(metadata=field_options(alias="temporalTitles"))
    availability: Availability
    category: Category
    usage_rights: UsageRights = field(metadata=field_options(alias="usageRights"))
    production_year: int = field(metadata=field_options(alias="productionYear"))
    duration: Duration
    index_points: list[IndexPoint] = field(metadata=field_options(alias="indexPoints"))
    playlist: list[PlaylistItem] = field(metadata=field_options(alias="playlist"))
