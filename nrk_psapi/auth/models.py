from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import NotRequired, TypedDict, get_type_hints

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin
from typing_extensions import TypedDict as TypedDictFunc

from nrk_psapi.models.common import StrEnum


@dataclass
class NrkUserLoginDetails:
    """Represents user's login details for NRK authentication."""

    email: str
    password: str


class ContextInfo(TypedDict):
    clientId: str
    authority: str


class HashingAlgorithm(TypedDict):
    algorithm: str
    n: NotRequired[int]
    r: NotRequired[int]
    p: NotRequired[int]
    dkLen: NotRequired[int]


class NrkIdentityType(StrEnum):
    USER = "User"
    PROFILE = "Profile"


class NrkProfileType(StrEnum):
    CHILD = "Child"
    ADULT = "Adult"


class LoginState(StrEnum):
    LOGGED_IN = "LoggedIn"
    LOGGED_OUT = "LoggedOut"
    UNKNOWN = "Unknown"


@dataclass
class HashingRecipe(DataClassORJSONMixin):
    algorithm: str
    salt: str | None


@dataclass
class HashingInstructions(DataClassORJSONMixin):
    current: HashingRecipe
    next: HashingRecipe | None


HashingRecipeDict = TypedDictFunc("HashingRecipeDict", dict(get_type_hints(HashingRecipe).items()))  # noqa: UP013


@dataclass
class NrkClaims(DataClassORJSONMixin):
    sub: str
    nrk_profile_type: NrkProfileType = field(metadata=field_options(alias="nrk/profile_type"))
    nrk_identity_type: NrkIdentityType = field(metadata=field_options(alias="nrk/identity_type"))
    name: str
    given_name: str
    family_name: str
    email_verified: bool
    gender: str
    birth_year: str
    zip_code: str
    nrk_age: str = field(metadata=field_options(alias="nrk/age"))
    email: str
    nrk_cor: str = field(metadata=field_options(alias="nrk/cor"))
    nrk_cor_exp: str = field(metadata=field_options(alias="nrk/cor_exp"))
    nrk_consent_prof: str = field(metadata=field_options(alias="nrk/consent/prof"))
    nrk_consent_portability: str = field(metadata=field_options(alias="nrk/consent/portability"))
    nrk_consent_forum: str = field(metadata=field_options(alias="nrk/consent/forum"))
    nrk_consent_cont: str = field(metadata=field_options(alias="nrk/consent/cont"))
    nrk_news_region: str = field(metadata=field_options(alias="nrk/news_region"))
    nrk_sapmi: str = field(metadata=field_options(alias="nrk/sapmi"))
    nrk_cg: str = field(metadata=field_options(alias="nrk/cg"))
    nrk_age_limit: str = field(metadata=field_options(alias="nrk/age_limit"))


@dataclass
class NrkIdentity(DataClassORJSONMixin):
    sub: str
    name: str
    short_name: str = field(metadata=field_options(alias="shortName"))
    profile_type: NrkProfileType = field(metadata=field_options(alias="profileType"))
    identity_type: NrkIdentityType = field(metadata=field_options(alias="identityType"))
    birth_date: str | None = field(default=None, metadata=field_options(alias="birthDate"))
    age: int | None = None
    avatar: str | None = None
    color: str | None = None
    age_limit: str | None = field(default=None, metadata=field_options(alias="ageLimit"))
    email: str | None = None
    belongs_to: list[str] = field(default=None, metadata=field_options(alias="belongsTo"))


@dataclass
class NrkUser(DataClassORJSONMixin):
    sub: str
    name: str
    email: str
    profile_type: NrkProfileType = field(metadata=field_options(alias="profileType"))
    identity_type: NrkIdentityType = field(metadata=field_options(alias="identityType"))
    claims: NrkClaims
    news_region: str = field(metadata=field_options(alias="newsRegion"))
    sapmi: bool
    color: str | None = None
    avatar: str | None = None


@dataclass
class LoginSession(DataClassORJSONMixin):
    user: NrkUser
    server_epoch_expiry: datetime = field(
        metadata=field_options(
            alias="serverEpochExpiry",
            deserialize=lambda x: datetime.fromtimestamp(x, tz=timezone.utc),
            serialize=lambda x: x.timestamp(),
        )
    )
    expires_in: int = field(metadata=field_options(alias="expiresIn"))
    soft_expires_in: int = field(metadata=field_options(alias="softExpiresIn"))
    identities: list[NrkIdentity]
    access_token: str = field(metadata=field_options(alias="accessToken"))
    id_token: str = field(metadata=field_options(alias="idToken"))
    user_problem: str | None = field(metadata=field_options(alias="userProblem"))


@dataclass
class NrkAuthCredentials(DataClassORJSONMixin):
    session: LoginSession
    state: LoginState
    user_action: str | None = field(default=None, metadata=field_options(alias="userAction"))
    nrk_login: str | None = None

    @property
    def access_token(self) -> str:
        return self.session.access_token

    @property
    def id_token(self) -> str:
        return self.session.id_token

    def is_expired(self) -> bool:
        return self.session.server_epoch_expiry < datetime.now(tz=timezone.utc)

    def authenticated_headers(self):
        return {
            "authorization": f"Bearer {self.access_token}",
        }
