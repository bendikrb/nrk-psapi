# NrkPodcastAPI

NrkPodcastAPI is a Python library for interacting with the NRK Podcast API. It provides a simple interface for retrieving podcast information and episode details.

## Installation

To install the library, you can use pip:

```
pip install nrk-psapi
```

## Usage

Here's an example of how to use the library to retrieve information about a podcast:

```python
from nrk_psapi import NrkPodcastAPI

api = NrkPodcastAPI()
podcast = api.get_podcast("podcast_id")
print(podcast.title)
```

You can also retrieve information about an episode:

```python
episode = api.get_episode("podcast_id", "episode_id")
print(episode.title)
```

## Contributing

If you'd like to contribute to the project, please submit a pull request or open an issue on the GitHub repository.

## License

NrkPodcastAPI is licensed under the MIT license. See the LICENSE file for more details.

## Contact

If you have any questions or need assistance with the library, you can contact the project maintainer at @bendikrb.
