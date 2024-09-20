"""Tests for NrkPodcastAPI caching."""

from unittest.mock import MagicMock

import diskcache


async def test_get_cache(test_cache):
    import nrk_psapi

    memory = nrk_psapi.get_cache()
    assert isinstance(memory, diskcache.Cache)

    store = list()

    @test_cache
    def f(x):
        store.append(1)
        return x

    f(1)
    store_size = len(store)

    f(1)
    assert len(store) == store_size

    f(2)
    assert len(store) == store_size + 1


async def test_clear_cache(test_cache):
    """Make sure that we can clear the cache."""
    import nrk_psapi

    store = list()

    @test_cache
    def f(x):
        store.append(1)
        return x

    f(1)
    store_size = len(store)
    f(1)
    assert len(store) == store_size

    nrk_psapi.clear_cache()
    f(1)
    assert len(store) == store_size + 1


async def test_disable_cache(test_cache):
    """Make sure that we can disable the cache."""
    import nrk_psapi

    nrk_psapi.disable_cache()

    store = list()

    @test_cache
    def f(x):
        store.append(1)
        return x

    f(1)
    store_size = len(store)
    f(1)
    assert len(store) == store_size + 1


async def test_cache_disabled_decorator(test_cache):
    """Ensure cache can be disabled in a local scope"""

    from nrk_psapi.caching import cache_disabled

    mock = MagicMock()

    @test_cache
    def fn():
        mock()
        return 1

    fn()
    assert mock.call_count == 1

    fn()
    assert mock.call_count == 1

    with cache_disabled():
        fn()
    assert mock.call_count == 2

    fn()
    assert mock.call_count == 2
