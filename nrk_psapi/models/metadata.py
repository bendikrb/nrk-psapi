from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta  # noqa: TCH003

from isodate import duration_isoformat, parse_duration
from mashumaro import field_options

from .catalog import Image, IndexPoint, Link, Links, Titles  # noqa: TCH001
from .common import BaseDataClassORJSONMixin
from .playback import Playable  # noqa: TCH001


@dataclass
class LegalAgeRating(BaseDataClassORJSONMixin):
    """Represents the rating information for legal age."""

    code: str
    display_age: str = field(metadata=field_options(alias="displayAge"))
    display_value: str = field(metadata=field_options(alias="displayValue"))


@dataclass
class LegalAgeBody(BaseDataClassORJSONMixin):
    """Represents the body of legal age information."""

    status: str
    rating: LegalAgeRating


@dataclass
class LegalAge(BaseDataClassORJSONMixin):
    """Represents the legal age information."""

    legal_reference: str = field(metadata=field_options(alias="legalReference"))
    body: LegalAgeBody


@dataclass
class OnDemand(BaseDataClassORJSONMixin):
    """Represents the on demand information."""

    _from: datetime = field(metadata=field_options(alias="from"))
    to: datetime
    has_rights_now: bool = field(metadata=field_options(alias="hasRightsNow"))

@dataclass
class Availability(BaseDataClassORJSONMixin):
    """Represents the availability information."""

    information: str
    is_geo_blocked: bool = field(metadata=field_options(alias="isGeoBlocked"))
    on_demand: OnDemand = field(metadata=field_options(alias="onDemand"))
    external_embedding_allowed: bool = field(metadata=field_options(alias="externalEmbeddingAllowed"))
    live: dict[str, str] | None = None

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
class Podcast(BaseDataClassORJSONMixin):
    """Represents the podcast information in the _embedded section."""

    _links: dict[str, Link]
    titles: Titles
    image_url: str = field(metadata=field_options(alias="imageUrl"))
    rss_feed: str = field(metadata=field_options(alias="rssFeed"))
    episode_count: int = field(metadata=field_options(alias="episodeCount"))


@dataclass
class PodcastEpisode(BaseDataClassORJSONMixin):
    """Represents the podcast episode information in the _embedded section."""

    clip_id: str | None = field(default=None, metadata=field_options(alias="clipId"))


@dataclass
class Embedded(BaseDataClassORJSONMixin):
    """Represents the _embedded section in the API response."""

    manifests: list[Manifest]
    podcast: Podcast
    podcast_episode: PodcastEpisode = field(metadata=field_options(alias="podcastEpisode"))
    next: dict | None = None
    previous: dict | None = None


@dataclass
class PodcastMetadata(BaseDataClassORJSONMixin):
    """Represents the main structure of the API response for podcast metadata."""

    _links: Links
    id: str
    playability: str
    streaming_mode: str = field(metadata=field_options(alias="streamingMode"))
    duration: timedelta = field(metadata=field_options(deserialize=parse_duration, serialize=duration_isoformat))
    legal_age: LegalAge = field(metadata=field_options(alias="legalAge"))
    availability: Availability
    preplay: Preplay
    playable: Playable
    source_medium: str = field(metadata=field_options(alias="sourceMedium"))
    _embedded: Embedded
    display_aspect_ratio: str | None = field(default=None, metadata=field_options(alias="displayAspectRatio"))
    non_playable: dict | None = field(default=None, metadata=field_options(alias="nonPlayable"))
    interaction_points: list | None = field(default=None, metadata=field_options(alias="interactionPoints"))
    skip_dialog_info: dict | None = field(default=None, metadata=field_options(alias="skipDialogInfo"))
    interaction: dict | None = None

