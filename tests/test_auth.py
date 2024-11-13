"""Tests for nrk_psapi auth."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aresponses import ResponsesMockServer
import pytest
import scrypt

from nrk_psapi import NrkAuthClient
from nrk_psapi.auth.utils import parse_hashing_algorithm

from .helpers import setup_auth_mocks

if TYPE_CHECKING:
    from nrk_psapi.auth.models import HashingRecipeDict


@pytest.mark.parametrize(
    ("password", "recipe", "expected_hash"),
    [
        (
            "abc123",
            {"algorithm": "cscrypt:10:8:1:32", "salt": "LqVSR09qZJdl5hlaukwKtA=="},
            "386cc9e637df3962649bdd1f3580099050f949a446a45ca887889fff94a39e27",
        ),
        (
            "Password123",
            {"algorithm": "cscrypt:10:8:1:32", "salt": "pQ7oJqGVQygr6gQLvfzA+g=="},
            "9e6815920eb3d32515e155880b1c1e16b65a2552c95083e5d437e6679fb6c7a3",
        ),
        (
            "Paèéßôöäë",
            {"algorithm": "cscrypt:10:8:1:32", "salt": "yKa28coeyThcwJkI7ON9qw=="},
            "0f83b199540a93f20bfeada6fdba9485f55598a5f4bd46f1d6fca743fc18c31d",
        ),
        (
            "æøå !@$",
            {"algorithm": "cscrypt:10:8:1:32", "salt": "bOiGKCF76VCpvtzlJwm1sA=="},
            "f56197370ce3326b4fd25eb349b89ce5272f6e09bfdca7e8994a0e4921d16d93",
        ),
        (
            "😣 😖 😫 😩 🥺 😢",
            {"algorithm": "cscrypt:10:8:1:32", "salt": "EUVQZ9z/pdSmOymhzUIj+Q=="},
            "60731ab8e13a1fd75e1a76c541b14cb4bbb9abe58b1cafb35c6498e052bce27e",
        ),
        (
            "中文鍵盤/中文键盘",
            {"algorithm": "cscrypt:10:8:1:32", "salt": "BhokTPCvxD2oNix2B5ugVA=="},
            "a723c9a905d0e812ceb47f88959e43364bee76ee589fb0b4bfb2e5c6a3218145",
        ),
        (
            "㊑",
            {"algorithm": "cscrypt:10:8:1:32", "salt": "xF9KfI+rD+EmWsAKLtsDPA=="},
            "21d9274fa6e9f9783b18727e0f8262c376553ac4f1c051a0a4229ec2033ba103",
        ),
    ],
)
async def test_password_hashing(password: str, recipe: HashingRecipeDict, expected_hash: str):
    algo = parse_hashing_algorithm(recipe["algorithm"])
    hashed_password = scrypt.hash(password, recipe["salt"], algo["n"], algo["r"], algo["p"], algo["dkLen"])
    assert hashed_password.hex() == expected_hash


async def test_async_get_access_token_with_valid_credentials(nrk_default_auth_client, default_credentials):
    async with nrk_default_auth_client() as auth_client:
        access_token = await auth_client.async_get_access_token()
        assert access_token == default_credentials.access_token

    async with NrkAuthClient(credentials=default_credentials) as auth_client:
        access_token = await auth_client.async_get_access_token()
        assert access_token == default_credentials.access_token


async def test_authorize_success(
    aresponses: ResponsesMockServer, nrk_default_auth_client, default_credentials, default_login_details
):
    setup_auth_mocks(aresponses, default_credentials)
    default_credentials_dict = default_credentials.to_dict()

    async with nrk_default_auth_client(load_default_credentials=False) as auth_client:
        token = await auth_client.async_get_access_token()
        credentials = auth_client.get_credentials()
        assert credentials == default_credentials_dict
        assert token == default_credentials.access_token
        credentials = await auth_client.authorize(default_login_details)
        assert credentials == default_credentials
