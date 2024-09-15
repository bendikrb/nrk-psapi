# nrk-psapi

[![GitHub Release][releases-shield]][releases]
[![Python Versions][py-versions-shield]][py-versions]
![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE.md)

[![Build Status][build-shield]][build]
[![Code coverage][codecov-shield]][codecov]


Asynchronous Python client for the NRK Podcast/Radio API

## Installation

```bash
pip install nrk-psapi
```

## Usage

The following are some basic examples of how to use the library.

Get information about a specific podcast:

```python
import asyncio

from nrk_psapi import NrkPodcastAPI


async def main():
    """Main function."""
    async with NrkPodcastAPI() as client:
        podcast = await client.get_podcast(podcast_id="desken_brenner")
        print(podcast)


if __name__ == "__main__":
    asyncio.run(main())
```

Get all episodes for a specific podcast:

```python
episodes = await client.get_podcast_episodes(podcast_id="desken_brenner")
for episode in episodes:
    print(episode)
```

Search for a specific podcast:

```python
search_results = await client.search(
    query="Norsk", search_type=SearchResultType.PODCAST
)
for result in search_results.hits:
    print(result)
```

Get curated podcasts:

```python
curated_podcasts = await client.curated_podcasts()
for section in curated_podcasts.sections:
    print(section)
    for podcast in section.podcasts:
        print(podcast)
```


## Contributing

If you'd like to contribute to the project, please submit a pull request or open an issue on the GitHub repository.

## License

nrk-psapi is licensed under the MIT license. See the LICENSE file for more details.

## Contact

If you have any questions or need assistance with the library, you can contact the project maintainer at @bendikrb.

[license-shield]: https://img.shields.io/github/license/bendikrb/nrk-psapi.svg
[license]: https://github.com/bendikrb/nrk-psapi/blob/main/LICENSE
[releases-shield]: https://img.shields.io/pypi/v/nrk-psapi
[releases]: https://github.com/bendikrb/nrk-psapi/releases
[build-shield]: https://github.com/bendikrb/nrk-psapi/actions/workflows/test.yaml/badge.svg
[build]: https://github.com/bendikrb/nrk-psapi/actions/workflows/tests.yaml
[maintenance-shield]: https://img.shields.io/maintenance/yes/2024.svg
[py-versions-shield]: https://img.shields.io/pypi/pyversions/nrk-psapi
[py-versions]: https://pypi.org/project/nrk-psapi/
[codecov-shield]: https://codecov.io/gh/bendikrb/nrk-psapi/graph/badge.svg?token=011O5N9MKL
[codecov]: https://codecov.io/gh/bendikrb/nrk-psapi
