from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta  # noqa: TCH003

from isodate import duration_isoformat, parse_duration
from mashumaro import field_options

from .catalog import Image, IndexPoint, Link, Links, Titles
from .common import BaseDataClassORJSONMixin, StrEnum, T
from .playback import (
    AvailabilityDetailed,
    NonPlayable,
    Playability,
    Playable,
    PlayableSourceMedium,
)


class InteractionPoint(StrEnum):
    SEEK_TO_POINTS = "seekToPoints"
    NEXT_UP_POINT = "nextUpPoint"
    RECOMMEND_NEXT_POINT = "recommendNextPoint"


@dataclass
class Interaction(BaseDataClassORJSONMixin):
    type: InteractionPoint
    start_time: float = field(metadata=field_options(alias="startTime"))
    end_time: float = field(metadata=field_options(alias="endTime"))

    def __str__(self):
        return f"{self.type}: {self.start_time} - {self.end_time}"


@dataclass
class LegalAgeRating(BaseDataClassORJSONMixin):
    """Represents the rating information for legal age."""

    code: str
    display_age: str = field(metadata=field_options(alias="displayAge"))
    display_value: str = field(metadata=field_options(alias="displayValue"))

    def __str__(self) -> str:
        return f"{self.display_value}"


@dataclass
class LegalAgeBody(BaseDataClassORJSONMixin):
    """Represents the body of legal age information."""

    status: str
    rating: LegalAgeRating | None = None

    def __str__(self) -> str:
        return f"{self.rating or self.status}"


@dataclass
class LegalAge(BaseDataClassORJSONMixin):
    """Represents the legal age information."""

    legal_reference: str = field(metadata=field_options(alias="legalReference"))
    body: LegalAgeBody

    def __str__(self) -> str:
        return f"[{self.legal_reference}] {self.body}"


@dataclass
class OnDemand(BaseDataClassORJSONMixin):
    """Represents the on demand information."""

    _from: datetime = field(metadata=field_options(alias="from"))
    to: datetime
    has_rights_now: bool = field(metadata=field_options(alias="hasRightsNow"))


@dataclass
class Poster(BaseDataClassORJSONMixin):
    """Represents a poster with multiple image sizes."""

    images: list[Image]


@dataclass
class SkipDialogInfo(BaseDataClassORJSONMixin):
    start_intro_in_seconds: int = field(metadata=field_options(alias="startIntroInSeconds"))
    end_intro_in_seconds: int = field(metadata=field_options(alias="endIntroInSeconds"))
    start_credits_in_seconds: int = field(metadata=field_options(alias="startCreditsInSeconds"))
    start_intro: timedelta = field(
        metadata=field_options(alias="startIntro", deserialize=parse_duration, serialize=duration_isoformat)
    )
    end_intro: timedelta = field(
        metadata=field_options(alias="endIntro", deserialize=parse_duration, serialize=duration_isoformat)
    )
    start_credits: timedelta = field(
        metadata=field_options(alias="startCredits", deserialize=parse_duration, serialize=duration_isoformat)
    )


@dataclass
class Preplay(BaseDataClassORJSONMixin):
    """Represents the preplay information."""

    titles: Titles
    description: str
    poster: Poster
    index_points: list[IndexPoint] = field(metadata=field_options(alias="indexPoints"))
    square_poster: Poster | None = field(default=None, metadata=field_options(alias="squarePoster"))


@dataclass
class Manifest(BaseDataClassORJSONMixin):
    """Represents a manifest in the _embedded section."""

    _links: Links
    availability_label: str = field(metadata=field_options(alias="availabilityLabel"))
    id: str

    def __str__(self):
        return f"{self.id} ({self.availability_label})"


@dataclass
class PodcastMetadataEmbedded(BaseDataClassORJSONMixin):
    """Represents the podcast information in the _embedded section."""

    _links: dict[str, Link]
    titles: Titles
    image_url: str = field(metadata=field_options(alias="imageUrl"))
    rss_feed: str = field(metadata=field_options(alias="rssFeed"))
    episode_count: int = field(metadata=field_options(alias="episodeCount"))


@dataclass
class PodcastEpisodeMetadata(BaseDataClassORJSONMixin):
    """Represents the podcast episode information in the _embedded section."""

    clip_id: str | None = field(default=None, metadata=field_options(alias="clipId"))


@dataclass
class PodcastMetadata(BaseDataClassORJSONMixin):
    """Represents the main structure of the API response for podcast metadata."""

    _links: Links
    id: str
    playability: Playability
    streaming_mode: str = field(metadata=field_options(alias="streamingMode"))
    legal_age: LegalAge = field(metadata=field_options(alias="legalAge"))
    availability: AvailabilityDetailed
    preplay: Preplay
    source_medium: PlayableSourceMedium = field(metadata=field_options(alias="sourceMedium"))
    duration: timedelta | None = field(
        default=None, metadata=field_options(deserialize=parse_duration, serialize=duration_isoformat)
    )
    display_aspect_ratio: str | None = field(default=None, metadata=field_options(alias="displayAspectRatio"))
    playable: Playable | None = field(default=None)
    non_playable: NonPlayable | None = field(default=None, metadata=field_options(alias="nonPlayable"))
    interaction_points: list[InteractionPoint] | None = field(
        default_factory=list, metadata=field_options(alias="interactionPoints")
    )
    skip_dialog_info: SkipDialogInfo | None = field(
        default=None, metadata=field_options(alias="skipDialogInfo")
    )
    interaction: list[Interaction] | None = field(default_factory=list)

    manifests: list[Manifest] = field(default_factory=list)
    podcast: PodcastMetadataEmbedded | None = field(default=None)
    podcast_episode: PodcastEpisodeMetadata | None = field(default=None)

    @classmethod
    def __pre_deserialize__(cls: type[T], d: T) -> T:
        d["manifests"] = d.get("_embedded", {}).get("manifests")
        d["podcast"] = d.get("_embedded", {}).get("podcast")
        d["podcast_episode"] = d.get("_embedded", {}).get("podcastEpisode")
        return d
