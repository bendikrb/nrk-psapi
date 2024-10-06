from __future__ import annotations

from dataclasses import dataclass, field
from typing import NotRequired, TypedDict, get_type_hints

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin
from typing_extensions import TypedDict as TypedDictFunc


class ContextInfo(TypedDict):
    clientId: str
    authority: str


class HashingAlgorithm(TypedDict):
    algorithm: str
    n: NotRequired[int]
    r: NotRequired[int]
    p: NotRequired[int]
    dkLen: NotRequired[int]


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
