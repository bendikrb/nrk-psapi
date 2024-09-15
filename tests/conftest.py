import logging

import pytest

_LOGGER = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption(
        "--update-fixtures",
        action="store_true",
        default=False,
        help="Save updated fixtures",
    )


@pytest.fixture
def update_fixtures(request):
    return request.config.getoption("update_fixtures")
