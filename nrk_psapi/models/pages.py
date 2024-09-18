from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta  # noqa: TCH003
from typing import TYPE_CHECKING, Literal

from isodate import duration_isoformat, parse_duration
from mashumaro import field_options
from mashumaro.config import BaseConfig
from mashumaro.types import Discriminator
from rich.table import Table

from nrk_psapi.utils import sanitize_string

from .catalog import Link, Titles, WebImage
from .common import BaseDataClassORJSONMixin, StrEnum

if TYPE_CHECKING:
    from rich.console import Console, ConsoleOptions, RenderResult


class DisplayType(StrEnum):
    DEFAULT = "default"
    GRID = "grid"


# noinspection SpellCheckingInspection
class DisplayContract(StrEnum):
    HERO = "hero"
    EDITORIAL = "editorial"
    INLINEHERO = "inlineHero"
    LANDSCAPE = "landscape"
    LANDSCAPELOGO = "landscapeLogo"
    SIMPLE = "simple"
    SQUARED = "squared"
    SQUAREDLOGO = "squaredLogo"
    NYHETSATOM = "nyhetsAtom"
    RADIOMULTIHERO = "radioMultiHero"
    SIDEKICKLOGO = "sidekickLogo"


class PlugSize(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


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
    CATEGORY = "category"
    SUBCATEGORY = "subcategory"


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
    product_custom_dimensions: ProductCustomDimensions = field(
        metadata=field_options(alias="productCustomDimensions")
    )


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

    def __str__(self):
        return str(self.external_url)


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
class PluggedEpisode(BaseDataClassORJSONMixin):
    title: str = field(init=False)
    titles: Titles
    image: WebImage
    duration: timedelta = field(
        metadata=field_options(deserialize=parse_duration, serialize=duration_isoformat)
    )
    series: PluggedSeries | None = None

    def __post_init__(self):
        self.title = self.titles.title


@dataclass
class PluggedSeries(BaseDataClassORJSONMixin):
    title: str = field(init=False)
    titles: Titles
    image: WebImage | None = None
    number_of_episodes: int | None = field(default=None, metadata=field_options(alias="numberOfEpisodes"))

    def __post_init__(self):
        self.title = self.titles.title


@dataclass
class PluggedChannel(BaseDataClassORJSONMixin):
    title: str = field(init=False)
    titles: Titles
    image: WebImage | None = None

    def __post_init__(self):
        self.title = self.titles.title


@dataclass
class PluggedStandaloneProgram(BaseDataClassORJSONMixin):
    title: str = field(init=False)
    titles: Titles
    image: WebImage
    duration: timedelta = field(
        metadata=field_options(deserialize=parse_duration, serialize=duration_isoformat)
    )

    def __post_init__(self):
        self.title = self.titles.title


@dataclass
class PluggedPodcast(BaseDataClassORJSONMixin):
    podcast_title: str = field(init=False)
    titles: Titles
    image_url: str | None = field(default=None, metadata=field_options(alias="imageUrl"))
    number_of_episodes: int | None = field(default=None, metadata=field_options(alias="numberOfEpisodes"))

    def __post_init__(self):
        self.podcast_title = self.titles.title


@dataclass
class PluggedPodcastEpisode(BaseDataClassORJSONMixin):
    title: str = field(init=False)
    titles: Titles
    duration: timedelta = field(
        metadata=field_options(deserialize=parse_duration, serialize=duration_isoformat)
    )
    image_url: str = field(metadata=field_options(alias="imageUrl"))
    podcast: PluggedPodcast
    podcast_title: str = field(init=False)

    def __post_init__(self):
        self.title = self.titles.title
        self.podcast_title = self.podcast.podcast_title


@dataclass
class PluggedPodcastSeason(BaseDataClassORJSONMixin):
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

    def __str__(self):
        return str(self._links)


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
    id: str = field(init=False)
    type = PlugType.CHANNEL
    _links: ChannelPlugLinks
    channel: PluggedChannel

    def __post_init__(self):
        self.id = self._links.channel.split("/").pop()

    # noinspection PyUnusedLocal
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.type}[/b]"
        table = Table("Attribute", "Value")
        table.add_row("id", self.id)
        table.add_row("channel.title", self.channel.title)
        yield table


@dataclass
class SeriesPlug(Plug):
    id: str = field(init=False)
    title: str = field(init=False)
    type = PlugType.SERIES
    _links: SeriesPlugLinks
    series: PluggedSeries

    def __post_init__(self):
        self.id = self._links.series.split("/").pop()
        self.title = self.series.title

    # noinspection PyUnusedLocal
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.type}[/b]"
        table = Table("Attribute", "Value")
        table.add_row("id", self.id)
        table.add_row("series.title", self.series.title)
        table.add_row("series.tagline", self.series.titles.subtitle)
        table.add_row("series.number_of_episodes", str(self.series.number_of_episodes))
        yield table


@dataclass
class EpisodePlug(Plug):
    id: str = field(init=False)
    series_id: str = field(init=False)
    title: str = field(init=False)
    type = PlugType.EPISODE
    _links: EpisodePlugLinks
    episode: PluggedEpisode

    def __post_init__(self):
        self.id = self._links.episode.split("/").pop()
        self.series_id = self._links.series.split("/").pop()
        self.title = self.episode.title

    # noinspection PyUnusedLocal
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.type}[/b]"
        table = Table("Attribute", "Value")
        table.add_row("id", self.id)
        table.add_row("series_id", self.series_id)
        table.add_row("episode.title", self.episode.title)
        yield table


@dataclass
class StandaloneProgramPlug(Plug):
    id: str = field(init=False)
    type = PlugType.STANDALONE_PROGRAM
    _links: StandaloneProgramPlugLinks
    program: PluggedStandaloneProgram

    def __post_init__(self):
        self.id = self._links.program.split("/").pop()

    # noinspection PyUnusedLocal
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.type}[/b]"
        table = Table("Attribute", "Value")
        table.add_row("id", self.id)
        table.add_row("program.title", self.program.title)
        table.add_row("program.duration", str(self.program.duration))
        yield table


@dataclass
class PodcastPlug(Plug):
    id: str = field(init=False)
    title: str = field(init=False)
    tagline: str = field(init=False)
    type = PlugType.PODCAST
    podcast: PluggedPodcast
    _links: PodcastPlugLinks

    def __post_init__(self):
        self.id = self._links.podcast.split("/").pop()
        self.title = self.podcast.podcast_title
        self.tagline = self.podcast.titles.subtitle

    # noinspection PyUnusedLocal
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.type}[/b]"
        table = Table("Attribute", "Value")
        table.add_row("id", self.id)
        table.add_row("title", self.title)
        table.add_row("tagline", self.tagline)
        table.add_row("podcast.number_of_episodes", str(self.podcast.number_of_episodes))
        yield table


@dataclass
class PodcastEpisodePlug(Plug):
    id: str = field(init=False)
    podcast_id: str = field(init=False)
    type = PlugType.PODCAST_EPISODE
    podcast_episode: PluggedPodcastEpisode = field(metadata=field_options(alias="podcastEpisode"))
    _links: PodcastEpisodePlugLinks

    def __post_init__(self):
        self.id = self._links.podcast_episode.split("/").pop()
        self.podcast_id = self._links.podcast.split("/").pop()

    # noinspection PyUnusedLocal
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.type}[/b]"
        table = Table("Attribute", "Value")
        table.add_row("id", self.id)
        table.add_row("podcast_id", self.podcast_id)
        table.add_row("podcast_episode.title", self.podcast_episode.title)
        yield table


@dataclass
class PodcastSeasonPlug(Plug):
    type = PlugType.PODCAST_SEASON
    id: str
    podcast_season: PluggedPodcastSeason = field(metadata=field_options(alias="podcastSeason"))
    image: WebImage | None = None

    # noinspection PyUnusedLocal
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.type}[/b]"
        table = Table("Attribute", "Value")
        table.add_row("id", self.id)
        table.add_row("podcast_season", str(self.podcast_season))
        yield table


@dataclass
class LinkPlug(Plug):
    type = PlugType.LINK
    link: LinkPlugInner
    id: str | None = None
    image: WebImage | None = None

    # noinspection PyUnusedLocal
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.type}[/b]"
        table = Table("Attribute", "Value")
        table.add_row("id", self.id)
        table.add_row("link", str(self.link))
        yield table


@dataclass
class PagePlug(Plug):
    type = PlugType.PAGE
    page: PagePlugInner
    id: str | None = None
    image: WebImage | None = None

    # noinspection PyUnusedLocal
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.type}[/b]"
        table = Table("Attribute", "Value")
        table.add_row("id", self.id)
        table.add_row("page", str(self.page))
        yield table


@dataclass
class Included(BaseDataClassORJSONMixin):
    section_id: str = field(init=False)
    title: str
    plugs: list[Plug]

    def __post_init__(self):
        self.section_id = sanitize_string(self.title, "-")


@dataclass
class IncludedSection(Section):
    type = SectionType.INCLUDED
    included: Included


@dataclass
class Page(BaseDataClassORJSONMixin):
    id: str = field(init=False)
    title: str
    sections: list[Section]
    _links: PageLinks

    def __post_init__(self):
        self.id = self._links.self.href.split("/").pop()


@dataclass
class CuratedPodcast(BaseDataClassORJSONMixin):
    id: str
    title: str
    subtitle: str
    image: str
    number_of_episodes: int


@dataclass
class CuratedSection(BaseDataClassORJSONMixin):
    id: str
    title: str
    podcasts: list[CuratedPodcast]


@dataclass
class Curated(BaseDataClassORJSONMixin):
    sections: list[CuratedSection]

    def get_section_by_id(self, section_id: str) -> CuratedSection | None:
        """Return the CuratedSection with the given id."""

        for section in self.sections:
            if section.id == section_id:
                return section
        return None
