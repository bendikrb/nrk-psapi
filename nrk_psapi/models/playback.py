from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta  # noqa: TCH003

from isodate import duration_isoformat, parse_duration
from mashumaro import field_options

from .catalog import Link
from .common import BaseDataClassORJSONMixin, DisplayAspectRatioVideo, StrEnum


class PlayableSourceMedium(StrEnum):
    AUDIO = "audio"
    VIDEO = "video"


class PlayableStreamingMode(StrEnum):
    LIVE = "live"
    ONDEMAND = "onDemand"


class Playability(StrEnum):
    PLAYABLE = "playable"
    NON_PLAYABLE = "nonPlayable"


@dataclass
class Live(BaseDataClassORJSONMixin):
    is_ongoing: bool = field(metadata=field_options(alias="isOngoing"))
    type: str
    transmission_interval: dict | None = field(
        default=None, metadata=field_options(alias="transmissionInterval")
    )


@dataclass
class AvailabilityDetailed(BaseDataClassORJSONMixin):
    """Represents the availability information."""

    information: str
    is_geo_blocked: bool = field(metadata=field_options(alias="isGeoBlocked"))
    external_embedding_allowed: bool = field(metadata=field_options(alias="externalEmbeddingAllowed"))
    on_demand: OnDemand | None = field(default=None, metadata=field_options(alias="onDemand"))
    live: Live | None = None

    def __str__(self):
        if self.on_demand:
            return str(self.on_demand)
        if self.live:
            return str(self.live)
        return self.information


@dataclass
class Links(BaseDataClassORJSONMixin):
    """Represents the _links object in the API response."""

    self: Link
    metadata: Link


@dataclass
class OnDemand(BaseDataClassORJSONMixin):
    """Represents the onDemand object in the availability section."""

    _from: datetime = field(metadata=field_options(alias="from"))
    to: datetime
    has_rights_now: bool = field(metadata=field_options(alias="hasRightsNow"))

    def __str__(self):
        return f"On demand: {self._from.isoformat()} - {self.to.isoformat()}"


@dataclass
class GaStatistics(BaseDataClassORJSONMixin):
    """Represents Google Analytics dimension data."""

    dimension1: str
    dimension2: str
    dimension3: str
    dimension4: str
    dimension5: str
    dimension10: str
    dimension21: str
    dimension22: str
    dimension23: str
    dimension25: str
    dimension26: str
    dimension29: str
    dimension36: str


@dataclass
class LunaConfig(BaseDataClassORJSONMixin):
    """Represents the Luna configuration."""

    beacon: str


@dataclass
class LunaData(BaseDataClassORJSONMixin):
    """Represents the Luna data."""

    title: str
    device: str
    player_id: str = field(metadata=field_options(alias="playerId"))
    delivery_type: str = field(metadata=field_options(alias="deliveryType"))
    player_info: str = field(metadata=field_options(alias="playerInfo"))
    cdn_name: str = field(metadata=field_options(alias="cdnName"))


@dataclass
class Luna(BaseDataClassORJSONMixin):
    """Represents the Luna statistics."""

    config: LunaConfig
    data: LunaData


@dataclass
class QualityOfExperience(BaseDataClassORJSONMixin):
    """Represents quality of experience statistics."""

    client_name: str = field(metadata=field_options(alias="clientName"))
    cdn_name: str = field(metadata=field_options(alias="cdnName"))
    streaming_format: str = field(metadata=field_options(alias="streamingFormat"))
    segment_length: str = field(metadata=field_options(alias="segmentLength"))
    asset_type: str = field(metadata=field_options(alias="assetType"))
    correlation_id: str = field(metadata=field_options(alias="correlationId"))


@dataclass
class Statistics(BaseDataClassORJSONMixin):
    """Represents various statistics for the podcast."""

    scores: dict | None = None
    ga: GaStatistics | None = None
    conviva: dict | None = None
    luna: Luna | None = None
    quality_of_experience: QualityOfExperience | None = field(
        default=None, metadata=field_options(alias="qualityOfExperience")
    )
    snowplow: dict[str, str] = field(default_factory=dict)


@dataclass
class Asset(BaseDataClassORJSONMixin):
    """Represents an asset in the playable content."""

    url: str
    format: str
    mime_type: str = field(metadata=field_options(alias="mimeType"))
    encrypted: bool

    def __str__(self) -> str:
        return f"{self.url} ({self.mime_type})"


@dataclass
class Playable(BaseDataClassORJSONMixin):
    """Represents the playable content information."""

    end_sequence_start_time: str | None = field(
        default=None, metadata=field_options(alias="endSequenceStartTime")
    )
    duration: timedelta | None = field(
        default=None,
        metadata=field_options(
            deserialize=parse_duration,
            serialize=duration_isoformat,
        ),
    )
    assets: list[Asset] | None = None
    live_buffer: dict | None = field(default=None, metadata=field_options(alias="liveBuffer"))
    subtitles: list | None = None
    thumbnails: list | None = None
    resolve: str | None = None

    def __str__(self) -> str:
        if self.resolve:
            return f"{self.resolve}"
        if self.assets:
            return "\n".join([str(x) for x in self.assets])
        return f"Playable({self.to_dict()})"


@dataclass
class NonPlayable(BaseDataClassORJSONMixin):
    """Represents the non-playable content information."""

    reason: str
    message_type: str | None = field(default=None, metadata=field_options(alias="messageType"))
    end_user_message: str | None = field(default=None, metadata=field_options(alias="endUserMessage"))
    end_user_message_supplement: str | None = field(
        default=None, metadata=field_options(alias="endUserMessageSupplement")
    )
    user_action: str | None = field(default=None, metadata=field_options(alias="userAction"))
    help_url: str | None = field(default=None, metadata=field_options(alias="helpUrl"))
    available_abroad_url: str | None = field(default=None, metadata=field_options(alias="availableAbroadUrl"))


@dataclass
class SkipDialogInfo(BaseDataClassORJSONMixin):
    start_intro_in_seconds: float = field(metadata=field_options(alias="startIntroInSeconds"))
    end_intro_in_seconds: float = field(metadata=field_options(alias="endIntroInSeconds"))
    start_credits_in_seconds: float = field(metadata=field_options(alias="startCreditsInSeconds"))
    start_intro: str = field(metadata=field_options(alias="startIntro"))
    end_intro: str = field(metadata=field_options(alias="endIntro"))
    start_credits: str = field(metadata=field_options(alias="startCredits"))


@dataclass
class PodcastManifest(BaseDataClassORJSONMixin):
    """Represents the main structure of the podcast manifest."""

    _links: Links
    id: str
    playability: Playability
    streaming_mode: PlayableStreamingMode = field(metadata=field_options(alias="streamingMode"))
    availability: AvailabilityDetailed
    statistics: Statistics
    source_medium: PlayableSourceMedium = field(metadata=field_options(alias="sourceMedium"))
    playable: Playable | None = field(default=None)
    non_playable: NonPlayable | None = field(default=None, metadata=field_options(alias="nonPlayable"))
    display_aspect_ratio: DisplayAspectRatioVideo | None = field(
        default=None, metadata=field_options(alias="displayAspectRatio")
    )
    skip_dialog_info: SkipDialogInfo | None = field(
        default=None, metadata=field_options(alias="skipDialogInfo")
    )
