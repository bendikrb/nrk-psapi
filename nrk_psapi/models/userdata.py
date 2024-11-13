from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime  # noqa: TCH003

from mashumaro import field_options

from .catalog import Link
from .common import BaseDataClassORJSONMixin, Enabled, StrEnum


class FavouriteSourceType(StrEnum):
    CONSUMED = "consumed"
    MANUAL = "manual"


class FavouriteType(StrEnum):
    PROGRAM = "program"
    SERIES = "series"
    PODCAST = "podcast"


class FavouriteLevel(StrEnum):
    AUTO = "auto"
    CONSUMED_FAVOURITES = "consumed_favourites"
    MANUAL_FAVOURITES = "manual_favourites"
    FAVOURITES_WITH_PUSH_NOTIFICATIONS = "favourites_with_push_notifications"


@dataclass
class UserFavouritesLinks(BaseDataClassORJSONMixin):
    self: Link
    next: Link | None = None


@dataclass
class UserFavouriteLinks(BaseDataClassORJSONMixin):
    self: Link
    share: Link
    delete_favourite: Link | None = field(default=None, metadata=field_options(alias="deleteFavourite"))
    unmark_favourite: Link | None = field(default=None, metadata=field_options(alias="unmarkFavourite"))
    push_notifications: Link | None = field(default=None, metadata=field_options(alias="pushNotifications"))


@dataclass
class UserFavourites(BaseDataClassORJSONMixin):
    _links: list[UserFavouritesLinks]
    id: str
    favourite_content_type: str = field(metadata=field_options(alias="favouriteContentType"))
    favourite_source: FavouriteSourceType = field(metadata=field_options(alias="favouriteSource"))
    push_notifications: Enabled = field(metadata=field_options(alias="pushNotifications"))
    _embedded: str = field(metadata=field_options(alias="_embedded"))


@dataclass
class UserFavourite(BaseDataClassORJSONMixin):
    _links: UserFavouriteLinks
    push_notifications: Enabled = field(metadata=field_options(alias="pushNotifications"))


@dataclass
class UserFavouritesResponse(BaseDataClassORJSONMixin):
    _links: UserFavouritesLinks
    favourites: list[UserFavourite]


@dataclass
class UserFavouriteNewEpisodesCountResponse(BaseDataClassORJSONMixin):
    count: int
    since: datetime
