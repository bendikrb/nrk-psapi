from __future__ import annotations

import contextlib
import logging
import os
import tempfile

import pytest

from nrk_psapi.api import NrkPodcastAPI
from nrk_psapi.auth import NrkAuthClient, NrkAuthCredentials, NrkUserLoginDetails

from .helpers import load_fixture_json

_LOGGER = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption(
        "--update-fixtures",
        action="store_true",
        default=False,
        help="Save updated fixtures",
    )


@pytest.fixture
def refresh_environment():  # noqa: PT004
    """Refresh the test environment."""
    import sys

    for key in list(sys.modules.keys()):
        if "nrk_psapi" in key:
            del sys.modules[key]
    with contextlib.suppress(KeyError):
        del os.environ["NRK_PSAPI_CACHE_DIR"]


@pytest.fixture
def test_cache(refresh_environment):
    """Initialize a temporary cache and delete it after the test has run."""
    with tempfile.TemporaryDirectory() as tempdir:
        os.environ["NRK_PSAPI_CACHE_DIR"] = tempdir
        import nrk_psapi

        memory = nrk_psapi.get_cache()
        assert memory.directory == tempdir

        yield nrk_psapi.caching.cache()

        memory.clear()


@pytest.fixture
async def nrk_client(default_credentials, default_login_details):
    """Return NRK api client."""

    @contextlib.asynccontextmanager
    async def _nrk_api_client(
        credentials: NrkAuthCredentials | None = None,
        load_default_credentials: bool = True,
        load_default_login_details: bool = False,
        conf_dir: str | None = None,
    ) -> NrkPodcastAPI:
        login_details = default_login_details if load_default_login_details is True else None
        auth_client = NrkAuthClient(login_details=login_details)
        if credentials is not None:
            auth_client.set_credentials(credentials)
        elif load_default_credentials:
            auth_client.set_credentials(default_credentials)
        disable_credentials_storage = conf_dir is None
        client = NrkPodcastAPI(
            auth_client=auth_client, disable_credentials_storage=disable_credentials_storage
        )
        try:
            await client.__aenter__()
            yield client
        finally:
            await client.__aexit__(None, None, None)

    return _nrk_api_client


@pytest.fixture
async def nrk_default_auth_client(default_login_details, default_credentials):
    """Return NrkAuthClient."""

    @contextlib.asynccontextmanager
    async def _nrk_auth_client(
        credentials: NrkAuthCredentials | None = None,
        login_details: NrkUserLoginDetails | None = None,
        load_default_credentials: bool = True,
        load_default_login_details: bool = True,
        **kwargs,
    ) -> NrkAuthClient:
        auth_client = NrkAuthClient(**kwargs)

        if login_details is not None:
            auth_client.login_details = login_details
        elif load_default_login_details:
            auth_client.login_details = default_login_details
        if credentials is not None:
            auth_client.set_credentials(credentials)
        elif load_default_credentials:
            auth_client.set_credentials(default_credentials)

        try:
            await auth_client.__aenter__()
            yield auth_client
        finally:
            await auth_client.__aexit__(None, None, None)

    return _nrk_auth_client


@pytest.fixture
def default_login_details():
    return NrkUserLoginDetails(email="testuser@example.com", password="securepassword123")  # noqa: S106


@pytest.fixture
def invalid_login_details():
    return NrkUserLoginDetails(email="testuser@fail.com", password="securepassword123")  # noqa: S106


@pytest.fixture
def default_credentials():
    data = load_fixture_json("auth_token")
    # data["expiration_time"] = int(datetime.now(tz=timezone.utc).timestamp() + data["expires_in"])
    return NrkAuthCredentials.from_dict(data)
