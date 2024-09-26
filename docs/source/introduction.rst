Introduction
============

The ``NrkPodcastAPI`` library provides an asynchronous interface to interact with the NRK Podcast API. It allows users to fetch podcast data, episodes, series, and more using a variety of methods.

Requirements
------------

Rich requires Python 3.11 and above.

Usage
-----

To use the ``NrkPodcastAPI``, you need to create an instance of the class and call its methods asynchronously.

Example:

.. code-block:: python

    import asyncio
    from nrk_psapi import NrkPodcastAPI

    async def main():
        async with NrkPodcastAPI(user_agent="YourApp/1.0") as api:
            podcasts = await api.get_all_podcasts()
            for podcast in podcasts:
                print(podcast.title)

    asyncio.run(main())


Logging
-------

The library uses a logger named ``nrk_psapi`` to log debug information. You can configure this logger to capture logs as needed.
