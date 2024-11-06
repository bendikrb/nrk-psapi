from __future__ import annotations

import contextlib
import logging
import os
import tempfile

import pytest

from nrk_psapi.auth import NrkAuthClient, NrkAuthData, NrkUserCredentials

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
async def nrk_default_auth_client(user_credentials, default_credentials):
    """Return NrkAuthClient."""

    @contextlib.asynccontextmanager
    async def _nrk_auth_client(
        credentials: NrkAuthData | None = None,
    ) -> NrkAuthClient:
        auth_client = NrkAuthClient()

        auth_client.user_credentials = user_credentials
        if credentials is not None:
            auth_client.set_credentials(credentials)

        try:
            await auth_client.__aenter__()
            yield auth_client
        finally:
            await auth_client.__aexit__(None, None, None)

    return _nrk_auth_client


@pytest.fixture
def user_credentials():
    return NrkUserCredentials(email="testuser@example.com", password="securepassword123")  # noqa: S106


@pytest.fixture
def default_credentials():
    data = load_fixture_json("auth_token")
    # data["expiration_time"] = int(datetime.now(tz=timezone.utc).timestamp() + data["expires_in"])
    return NrkAuthData.from_dict(data)
