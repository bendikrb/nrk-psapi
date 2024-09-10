import logging

import pytest

from nrk_psapi.api import NrkPodcastAPI

from .helpers import load_fixture, save_fixture

_LOGGER = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption("--save-fixtures", action="store_true", default=False, help="Save new fixtures")

@pytest.fixture
def save_fixtures(request):
    return request.config.getoption("save_fixtures")


@pytest.fixture
def mock_api_request(monkeypatch, save_fixtures):
    calls = []

    async def mock_request(self, uri, *args, **kwargs):  # noqa: ANN002
        fixture_name = uri.replace("/", "_")
        if save_fixtures:
            real_response = await self._real_request(uri, *args, **kwargs)
            save_fixture(fixture_name, real_response)
            calls.append((f"/{uri}", real_response))
            return real_response
        try:
            fixture_data = load_fixture(fixture_name)
            calls.append((f"/{uri}", fixture_data))
            return fixture_data
        except FileNotFoundError as err:
            raise ValueError(f"No fixture found for {uri}. Run with --save-fixtures to create it.") from err

    # noinspection PyProtectedMember
    monkeypatch.setattr("nrk_psapi.NrkPodcastAPI._real_request", NrkPodcastAPI._request, raising=False)  # noqa: SLF001
    # Replace _request with our mock
    monkeypatch.setattr("nrk_psapi.NrkPodcastAPI._request", mock_request)

    return calls

@pytest.fixture
def nrk_api(mock_api_request):
    return NrkPodcastAPI(user_agent="TestAgent")
