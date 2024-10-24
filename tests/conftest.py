import contextlib
import logging
import os
import tempfile

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
