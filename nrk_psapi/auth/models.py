from __future__ import annotations

from dataclasses import dataclass, field
from typing import NotRequired, TypedDict, get_type_hints

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin
from typing_extensions import TypedDict as TypedDictFunc

from nrk_psapi.models.common import StrEnum


@dataclass
class NrkUserCredentials:
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


@dataclass
class CSRF(DataClassORJSONMixin):
    name: str
    value: str


@dataclass
class LoginModel(DataClassORJSONMixin):
    csrf: CSRF = field(metadata=field_options(alias="csrf"))
    login_url: str = field(metadata=field_options(alias="loginUrl"))
    redirect_url: str = field(metadata=field_options(alias="redirectUrl"))
    client_side_hashing_recipe: HashingRecipe = field(metadata=field_options(alias="clientSideHashingRecipe"))
    client_id: str = field(metadata=field_options(alias="clientId"))
    protected_login_context_url: str = field(metadata=field_options(alias="protectedLoginContextUrl"))


@dataclass
class LoginFlowState(DataClassORJSONMixin):
    add_user: bool = field(metadata=field_options(alias="addUser"))
    terms_to_accept: str = field(metadata=field_options(alias="termsToAccept"))
    redirect_url: str = field(metadata=field_options(alias="redirectUrl"))
    encoded_redirect_url: str = field(metadata=field_options(alias="encodedRedirectUrl"))
    client_id: str = field(metadata=field_options(alias="clientId"))
    protected_login_context_url: str = field(metadata=field_options(alias="protectedLoginContextUrl"))
    # started_time: int = field(metadata=field_options(alias="startedTime"))
    exit_url: str = field(metadata=field_options(alias="exitUrl"))
    new_user_hash_algorithm: str = field(metadata=field_options(alias="newUserHashAlgorithm"))
    new_user_hash_salt: str = field(metadata=field_options(alias="newUserHashSalt"))
    model: LoginModel
    username: str | None = field(default=None, metadata=field_options(alias="username"))
    terms_addons_to_accept: str | None = field(
        default=None, metadata=field_options(alias="termsAddonsToAccept")
    )
    show_login_confirmation: bool | None = field(
        default=None, metadata=field_options(alias="showLoginConfirmation")
    )
    registration_context: str | None = field(
        default=None, metadata=field_options(alias="registrationContext")
    )


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
    server_epoch_expiry: int = field(metadata=field_options(alias="serverEpochExpiry"))
    expires_in: int = field(metadata=field_options(alias="expiresIn"))
    soft_expires_in: int = field(metadata=field_options(alias="softExpiresIn"))
    identities: list[NrkIdentity]
    access_token: str = field(metadata=field_options(alias="accessToken"))
    id_token: str = field(metadata=field_options(alias="idToken"))
    user_problem: str | None = field(metadata=field_options(alias="userProblem"))


@dataclass
class NrkAuthData(DataClassORJSONMixin):
    session: LoginSession
    state: LoginState
    user_action: str | None = field(default=None, metadata=field_options(alias="userAction"))
