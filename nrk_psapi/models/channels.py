from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from mashumaro import field_options

from .catalog import Image, Links
from .common import BaseDataClassORJSONMixin, StrEnum


def parse_duration(time_str: str):
    time_parts = time_str.split(":")
    return timedelta(hours=int(time_parts[0]), minutes=int(time_parts[1]), seconds=int(time_parts[2]))


def serialize_timedelta(duration: timedelta):
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f"{hours:02}:{minutes:02}:{seconds:02}"


class ChannelType(StrEnum):
    REGIONAL_CHANNEL = "regionalChannel"
    DISTRICT_CHANNEL = "districtChannel"


@dataclass
class ChannelImage(BaseDataClassORJSONMixin):
    aspect_ratio: str = field(metadata=field_options(alias="aspectRatio"))
    mime_type: str = field(metadata=field_options(alias="mimeType"))
    is_default_image: bool = field(metadata=field_options(alias="isDefaultImage"))
    images: list[Image]


@dataclass
class ChannelEntryImages(BaseDataClassORJSONMixin):
    main_key_art_image: ChannelImage | None = field(
        default=None, metadata=field_options(alias="mainKeyArtImage")
    )
    backdrop_image: ChannelImage | None = field(default=None, metadata=field_options(alias="backdropImage"))
    poster_image: ChannelImage | None = field(default=None, metadata=field_options(alias="posterImage"))
    square_image: ChannelImage | None = field(default=None, metadata=field_options(alias="squareImage"))


@dataclass
class ChannelEntry(BaseDataClassORJSONMixin):
    title: str
    program_id: str = field(metadata=field_options(alias="programId"))
    image: ChannelEntryImages
    actual_start: datetime = field(metadata=field_options(alias="actualStart"))
    actual_end: datetime = field(metadata=field_options(alias="actualEnd"))
    program_duration: timedelta = field(
        metadata=field_options(
            alias="programDuration",
            deserialize=parse_duration,
            serialize=serialize_timedelta,
        )
    )
    duration: timedelta = field(
        metadata=field_options(
            deserialize=parse_duration,
            serialize=serialize_timedelta,
        )
    )
    series_id: str | None = None


@dataclass
class DistrictChannel(BaseDataClassORJSONMixin):
    parent: str

    def __str__(self):
        return self.parent


@dataclass
class Channel(BaseDataClassORJSONMixin):
    id: str
    title: str
    type: ChannelType
    live_buffer_duration: timedelta = field(
        metadata=field_options(
            alias="liveBufferDuration",
            deserialize=parse_duration,
            serialize=serialize_timedelta,
        )
    )
    image: ChannelImage
    entries: list[ChannelEntry]
    district_channel: DistrictChannel | None = field(
        default=None, metadata=field_options(alias="districtChannel")
    )


@dataclass
class ChannelResponse(BaseDataClassORJSONMixin):
    _links: Links
    channel: Channel
