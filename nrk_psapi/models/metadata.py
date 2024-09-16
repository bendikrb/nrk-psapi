from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta  # noqa: TCH003

from isodate import duration_isoformat, parse_duration
from mashumaro import field_options

from .catalog import Image, IndexPoint, Link, Links, Titles  # noqa: TCH001
from .common import BaseDataClassORJSONMixin, T
from .playback import AvailabilityDetailed, Playable  # noqa: TCH001


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
    rating: LegalAgeRating

    def __str__(self) -> str:
        return f"{self.rating}"


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
class Preplay(BaseDataClassORJSONMixin):
    """Represents the preplay information."""

    titles: Titles
    description: str
    poster: Poster
    square_poster: Poster = field(metadata=field_options(alias="squarePoster"))
    index_points: list[IndexPoint] = field(metadata=field_options(alias="indexPoints"))


@dataclass
class Manifest(BaseDataClassORJSONMixin):
    """Represents a manifest in the _embedded section."""

    _links: Links
    availability_label: str = field(metadata=field_options(alias="availabilityLabel"))
    id: str


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
    playability: str
    streaming_mode: str = field(metadata=field_options(alias="streamingMode"))
    duration: timedelta = field(
        metadata=field_options(deserialize=parse_duration, serialize=duration_isoformat)
    )
    legal_age: LegalAge = field(metadata=field_options(alias="legalAge"))
    availability: AvailabilityDetailed
    preplay: Preplay
    playable: Playable
    source_medium: str = field(metadata=field_options(alias="sourceMedium"))
    display_aspect_ratio: str | None = field(
        default=None, metadata=field_options(alias="displayAspectRatio")
    )
    non_playable: dict | None = field(
        default=None, metadata=field_options(alias="nonPlayable")
    )
    interaction_points: list | None = field(
        default=None, metadata=field_options(alias="interactionPoints")
    )
    skip_dialog_info: dict | None = field(
        default=None, metadata=field_options(alias="skipDialogInfo")
    )
    interaction: dict | None = None

    manifests: list[Manifest] = field(default_factory=list)
    podcast: PodcastMetadataEmbedded | None = field(default=None)
    podcast_episode: PodcastEpisodeMetadata | None = field(default=None)

    @classmethod
    def __pre_deserialize__(cls: type[T], d: T) -> T:
        d["manifests"] = d.get("_embedded", {}).get("manifests")
        d["podcast"] = d.get("_embedded", {}).get("podcast")
        d["podcast_episode"] = d.get("_embedded", {}).get("podcastEpisode")
        return d
