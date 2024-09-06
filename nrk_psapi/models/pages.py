from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta  # noqa: TCH003
from typing import Literal

from isodate import duration_isoformat, parse_duration
from mashumaro import field_options
from mashumaro.config import BaseConfig
from mashumaro.types import Discriminator

from .catalog import Link, WebImage  # noqa: TCH001
from .common import BaseDataClassORJSONMixin, StrEnum


class DisplayType(StrEnum):
    DEFAULT = 'default'
    GRID = 'grid'


# noinspection SpellCheckingInspection
class DisplayContract(StrEnum):
    HERO = 'hero'
    EDITORIAL = 'editorial'
    INLINEHERO = 'inlineHero'
    LANDSCAPE = 'landscape'
    LANDSCAPELOGO = 'landscapeLogo'
    SIMPLE = 'simple'
    SQUARED = 'squared'
    SQUAREDLOGO = 'squaredLogo'
    NYHETSATOM = 'nyhetsAtom'
    RADIOMULTIHERO = 'radioMultiHero'
    SIDEKICKLOGO = 'sidekickLogo'


class PlugSize(StrEnum):
    SMALL = 'small'
    MEDIUM = 'medium'
    LARGE = 'large'


class PlugType(StrEnum):
    CHANNEL = "channel"
    SERIES = "series"
    EPISODE = "episode"
    STANDALONE_PROGRAM = "standaloneProgram"
    PODCAST = "podcast"
    PODCAST_EPISODE = "podcastEpisode"
    PODCAST_SEASON = "podcastSeason"
    LINK = "link"
    PAGE = "page"


class SectionType(StrEnum):
    INCLUDED = "included"
    PLACEHOLDER = "placeholder"


class PageTypeEnum(StrEnum):
    CATEGORY = 'category'
    SUBCATEGORY = 'subcategory'


@dataclass
class Placeholder(BaseDataClassORJSONMixin):
    type: str | None = None
    title: str | None = None


@dataclass
class PageEcommerce(BaseDataClassORJSONMixin):
    brand: str
    tracking_exempt: bool = field(metadata=field_options(alias="trackingExempt"))


@dataclass
class PlugEcommerce(BaseDataClassORJSONMixin):
    id: str
    name: str
    position: int


@dataclass
class PlugAnalytics(BaseDataClassORJSONMixin):
    content_id: str = field(metadata=field_options(alias="contentId"))
    content_source: str = field(metadata=field_options(alias="contentSource"))
    title: str | None = None


@dataclass
class ProductCustomDimensions(BaseDataClassORJSONMixin):
    dimension37: str
    dimension38: str | None = None
    dimension39: str | None = None


@dataclass
class TemplatedLink(BaseDataClassORJSONMixin):
    href: str
    templated: Literal[True] | None = None


@dataclass
class ButtonItem(BaseDataClassORJSONMixin):
    title: str
    page_id: str = field(metadata=field_options(alias="pageId"))
    url: str
    page_type: PageTypeEnum = field(metadata=field_options(alias="pageType"))


@dataclass
class SectionEcommerce(BaseDataClassORJSONMixin):
    list: str
    variant: str
    category: str
    product_custom_dimensions: ProductCustomDimensions = field(metadata=field_options(alias="productCustomDimensions"))


@dataclass
class StandaloneProgramLinks(BaseDataClassORJSONMixin):
    program: Link
    playback_metadata: Link = field(metadata=field_options(alias="playbackMetadata"))
    playback_manifest: Link = field(metadata=field_options(alias="playbackManifest"))
    share: Link


@dataclass
class PageListItemLinks(BaseDataClassORJSONMixin):
    self: Link


@dataclass
class PageLinks(BaseDataClassORJSONMixin):
    self: Link


@dataclass
class SeriesLinks(BaseDataClassORJSONMixin):
    series: Link
    share: Link
    favourite: TemplatedLink | None = None


@dataclass
class ChannelLinks(BaseDataClassORJSONMixin):
    playback_metadata: Link = field(metadata=field_options(alias="playbackMetadata"))
    playback_manifest: Link = field(metadata=field_options(alias="playbackManifest"))
    share: Link


@dataclass
class ChannelPlugLinks(BaseDataClassORJSONMixin):
    channel: str


@dataclass
class SeriesPlugLinks(BaseDataClassORJSONMixin):
    series: str


@dataclass
class PodcastPlugLinks(BaseDataClassORJSONMixin):
    podcast: str


@dataclass
class PodcastEpisodePlugLinks(BaseDataClassORJSONMixin):
    podcast_episode: str = field(metadata=field_options(alias="podcastEpisode"))
    podcast: str
    audio_download: str = field(metadata=field_options(alias="audioDownload"))


@dataclass
class EpisodePlugLinks(BaseDataClassORJSONMixin):
    episode: str
    mediaelement: str
    series: str
    season: str


@dataclass
class StandaloneProgramPlugLinks(BaseDataClassORJSONMixin):
    program: str
    mediaelement: str


@dataclass
class PodcastSeasonLinks(BaseDataClassORJSONMixin):
    podcast_season: Link = field(metadata=field_options(alias="podcastSeason"))
    podcast: Link
    share: Link
    favourite: TemplatedLink | None = None


@dataclass
class LinkPlugLinks(BaseDataClassORJSONMixin):
    external_url: Link = field(metadata=field_options(alias="externalUrl"))


@dataclass
class PagePlugLinks(BaseDataClassORJSONMixin):
    page_url: Link = field(metadata=field_options(alias="pageUrl"))


@dataclass
class Links(BaseDataClassORJSONMixin):
    self: Link


@dataclass
class Plug(BaseDataClassORJSONMixin):
    class Config(BaseConfig):
        discriminator = Discriminator(
            field="type",
            include_subtypes=True,
        )


@dataclass
class Section(BaseDataClassORJSONMixin):
    class Config(BaseConfig):
        discriminator = Discriminator(
            field="type",
            include_subtypes=True,
        )


@dataclass
class PlaceholderSection(Section):
    type = SectionType.PLACEHOLDER
    placeholder: Placeholder
    id: str | None = None
    e_commerce: SectionEcommerce | None = field(default=None, metadata=field_options(alias="eCommerce"))


@dataclass
class Episode(BaseDataClassORJSONMixin):
    titles: Titles
    image: WebImage
    duration: timedelta = field(metadata=field_options(deserialize=parse_duration, serialize=duration_isoformat))
    series: Series | None = None

    def __repr__(self):
        return f"[{self.titles.title}] ({self.series!s}"


@dataclass
class Series(BaseDataClassORJSONMixin):
    titles: Titles
    image: WebImage | None = None
    number_of_episodes: int | None = field(default=None, metadata=field_options(alias="numberOfEpisodes"))

    def __repr__(self):
        return f"[{self.titles.title}]"


@dataclass
class Channel(BaseDataClassORJSONMixin):
    titles: Titles
    image: WebImage | None = None

    def __repr__(self):
        return f"[{self.titles.title}]"


@dataclass
class StandaloneProgram(BaseDataClassORJSONMixin):
    titles: Titles
    image: WebImage
    duration: timedelta = field(metadata=field_options(deserialize=parse_duration, serialize=duration_isoformat))

    def __repr__(self):
        return f"[{self.titles.title}]"


@dataclass
class Titles(BaseDataClassORJSONMixin):
    title: str
    subtitle: str | None = None


@dataclass
class Podcast(BaseDataClassORJSONMixin):
    titles: Titles
    image_url: str | None = field(default=None, metadata=field_options(alias="imageUrl"))
    number_of_episodes: int | None = field(default=None, metadata=field_options(alias="numberOfEpisodes"))

    @property
    def podcast_title(self):
        return self.titles.title

    def __repr__(self):
        return f"[{self.podcast_title}]"


@dataclass
class PodcastEpisode(BaseDataClassORJSONMixin):
    titles: Titles
    duration: timedelta = field(metadata=field_options(deserialize=parse_duration, serialize=duration_isoformat))
    image_url: str = field(metadata=field_options(alias="imageUrl"))
    podcast: Podcast

    def __repr__(self):
        return f"[{self.podcast.podcast_title}] {self.titles.title}"


@dataclass
class PodcastSeason(BaseDataClassORJSONMixin):
    _links: PodcastSeasonLinks | None = None
    podcast_id: str | None = field(default=None, metadata=field_options(alias="podcastId"))
    season_id: str | None = field(default=None, metadata=field_options(alias="seasonId"))
    season_number: int | None = field(default=None, metadata=field_options(alias="seasonNumber"))
    number_of_episodes: int | None = field(default=None, metadata=field_options(alias="numberOfEpisodes"))
    image_url: str | None = field(default=None, metadata=field_options(alias="imageUrl"))
    podcast_title: str | None = field(default=None, metadata=field_options(alias="podcastTitle"))
    podcast_season_title: str | None = field(default=None, metadata=field_options(alias="podcastSeasonTitle"))


@dataclass
class LinkPlugInner(BaseDataClassORJSONMixin):
    _links: LinkPlugLinks


@dataclass
class PagePlugInner(BaseDataClassORJSONMixin):
    _links: PagePlugLinks
    page_id: str = field(metadata=field_options(alias="pageId"))


@dataclass
class PageListItem(BaseDataClassORJSONMixin):
    _links: PageListItemLinks
    title: str
    id: str | None = None
    image: WebImage | None = None
    image_square: WebImage | None = field(default=None, metadata=field_options(alias="imageSquare"))


@dataclass
class Pages(BaseDataClassORJSONMixin):
    _links: Links
    pages: list[PageListItem]


@dataclass
class ChannelPlug(Plug):
    type = PlugType.CHANNEL
    _links: ChannelPlugLinks
    channel: Channel

    @property
    def id(self):
        return self._links.channel.split('/').pop()

    def __repr__(self):
        return f"<{self.type}> {self.channel!s}"


@dataclass
class SeriesPlug(Plug):
    type = PlugType.SERIES
    _links: SeriesPlugLinks
    series: Series

    @property
    def id(self):
        return self._links.series.split('/').pop()

    def __repr__(self):
        return f"<{self.type}> {self.series!s}"


@dataclass
class EpisodePlug(Plug):
    type = PlugType.EPISODE
    _links: EpisodePlugLinks
    episode: Episode

    @property
    def id(self):
        return self._links.episode.split('/').pop()

    @property
    def series_id(self):
        return self._links.series.split('/').pop()

    def __repr__(self):
        return f"<{self.type}> {self.episode!s}"


@dataclass
class StandaloneProgramPlug(Plug):
    type = PlugType.STANDALONE_PROGRAM
    _links: StandaloneProgramPlugLinks
    program: StandaloneProgram

    @property
    def id(self):
        return self._links.program.split('/').pop()

    def __repr__(self):
        return f"<{self.type}> {self.program!s}"


@dataclass
class PodcastPlug(Plug):
    type = PlugType.PODCAST
    podcast: Podcast
    _links: PodcastPlugLinks

    @property
    def id(self):
        return self._links.podcast.split("/").pop()

    @property
    def links(self):
        return self._links

    @property
    def title(self):
        return self.podcast.podcast_title

    @property
    def tagline(self):
        return self.podcast.titles.subtitle

    def __repr__(self):
        return f"<{self.type}> {self.podcast!s}"


@dataclass
class PodcastEpisodePlug(Plug):
    type = PlugType.PODCAST_EPISODE
    podcast_episode: PodcastEpisode = field(metadata=field_options(alias="podcastEpisode"))
    _links: PodcastEpisodePlugLinks

    @property
    def id(self):
        return self._links.podcast_episode.split('/').pop()

    @property
    def podcast_id(self):
        return self._links.podcast.split('/').pop()

    def __repr__(self):
        return f"<{self.type}> {self.podcast_episode!s}"


@dataclass
class PodcastSeasonPlug(Plug):
    type = PlugType.PODCAST_SEASON
    id: str
    podcast_season: PodcastSeason = field(metadata=field_options(alias="podcastSeason"))
    image: WebImage | None = None

    def __repr__(self):
        return f"<{self.type}> {self.podcast_season!s}"


@dataclass
class LinkPlug(Plug):
    type = PlugType.LINK
    link: LinkPlugInner
    id: str | None = None
    image: WebImage | None = None

    def __repr__(self):
        return f"<{self.type}> {self.link!s}"


@dataclass
class PagePlug(Plug):
    type = PlugType.PAGE
    page: PagePlugInner
    id: str | None = None
    image: WebImage | None = None

    def __repr__(self):
        return f"<{self.type}> {self.page!s}"


@dataclass
class Included(BaseDataClassORJSONMixin):
    title: str
    plugs: list[Plug]


@dataclass
class IncludedSection(Section):
    type = SectionType.INCLUDED
    included: Included


@dataclass
class Page(BaseDataClassORJSONMixin):
    title: str
    sections: list[Section]
    _links: PageLinks

    @property
    def id(self) -> str:
        return self._links.self.href.split("/").pop()


@dataclass
class CuratedPodcast:
    id: str
    title: str
    subtitle: str
    image: str
    number_of_episodes: int


@dataclass
class CuratedSection:
    id: str
    title: str
    podcasts: list[CuratedPodcast]


@dataclass
class Curated:
    sections: list[CuratedSection]

    def get_section_by_id(self, section_id: str) -> CuratedSection | None:
        """Return the CuratedSection with the given id."""

        for section in self.sections:
            if section.id == section_id:
                return section
        return None
