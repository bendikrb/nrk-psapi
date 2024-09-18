from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta  # noqa: TCH003
from enum import Enum

from isodate import duration_isoformat, parse_duration
from mashumaro import field_options
from mashumaro.config import BaseConfig
from mashumaro.types import Discriminator

from .catalog import Links, Titles, WebImage
from .common import BaseDataClassORJSONMixin, StrEnum


class RecommendationType(str, Enum):
    PODCAST = "podcast"
    PODCAST_SEASON = "podcastSeason"
    PROGRAM = "program"
    SERIES = "series"

    def __str__(self) -> str:
        return str(self.value)


class RecommendationContext(StrEnum):
    """Give different recommendations based on which context (front page, series page, etc.) the user is in."""

    DEFAULT = "radio_viderenavigasjon_fra_program"


@dataclass
class UpstreamSystemInfoPayload(BaseDataClassORJSONMixin):
    id: str
    name: str
    brand: str
    list_id: str = field(metadata=field_options(alias="list"))
    position: int
    variant: str


@dataclass
class SnowplowSection(BaseDataClassORJSONMixin):
    id: str


@dataclass
class SnowplowContent(BaseDataClassORJSONMixin):
    id: str
    kind: str
    source: str


@dataclass
class Snowplow(BaseDataClassORJSONMixin):
    title: str
    section_index: int
    image_id: str
    recommendation_id: str
    section: SnowplowSection
    content: SnowplowContent


@dataclass
class UpstreamSystemInfo(BaseDataClassORJSONMixin):
    upstream_system: str = field(metadata=field_options(alias="upstreamSystem"))
    payload: UpstreamSystemInfoPayload


@dataclass
class RecommendedPodcast(BaseDataClassORJSONMixin):
    id: str
    titles: Titles
    image: WebImage
    number_of_episodes: int = field(metadata=field_options(alias="numberOfEpisodes"))
    square_image: WebImage = field(metadata=field_options(alias="squareImage"))


@dataclass
class RecommendedPodcastSeason(BaseDataClassORJSONMixin):
    id: str
    podcast_id: str = field(metadata=field_options(alias="podcastId"))
    titles: Titles
    image: WebImage
    season_number: int = field(metadata=field_options(alias="seasonNumber"))


@dataclass
class RecommendedSeries(BaseDataClassORJSONMixin):
    id: str
    titles: Titles
    image: WebImage
    number_of_episodes: int = field(metadata=field_options(alias="numberOfEpisodes"))
    square_image: WebImage | None = field(default=None, metadata=field_options(alias="squareImage"))


@dataclass
class RecommendedProgram(BaseDataClassORJSONMixin):
    id: str
    titles: Titles
    image: WebImage
    duration: timedelta = field(
        metadata=field_options(deserialize=parse_duration, serialize=duration_isoformat)
    )
    square_image: WebImage | None = field(default=None, metadata=field_options(alias="squareImage"))


@dataclass
class EmbeddedRecommendation(BaseDataClassORJSONMixin):
    _links: Links
    type: RecommendationType
    upstream_system_info: UpstreamSystemInfo = field(metadata=field_options(alias="upstreamSystemInfo"))

    class Config(BaseConfig):
        discriminator = Discriminator(
            field="type",
            include_subtypes=True,
        )


@dataclass
class EmbeddedPodcastRecommendation(EmbeddedRecommendation):
    type = RecommendationType.PODCAST
    podcast: RecommendedPodcast


@dataclass
class EmbeddedPodcastSeasonRecommendation(EmbeddedRecommendation):
    type = RecommendationType.PODCAST_SEASON
    podcast_season: RecommendedPodcastSeason = field(metadata=field_options(alias="podcastSeason"))


@dataclass
class EmbeddedSeriesRecommendation(EmbeddedRecommendation):
    type = RecommendationType.SERIES
    series: RecommendedSeries


@dataclass
class EmbeddedProgramRecommendation(EmbeddedRecommendation):
    type = RecommendationType.PROGRAM
    program: RecommendedProgram


@dataclass
class Recommendation(BaseDataClassORJSONMixin):
    _links: Links
    recommendations: list[EmbeddedRecommendation] = field(
        default_factory=list,
        metadata=field_options(
            alias="_embedded",
            deserialize=lambda x: [EmbeddedRecommendation.from_dict(d) for d in x["recommendations"]],
        ),
    )
