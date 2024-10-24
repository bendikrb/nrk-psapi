from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta  # noqa: TCH003
from typing import TYPE_CHECKING, Literal

from isodate import duration_isoformat, parse_duration
from mashumaro import field_options
from mashumaro.config import BaseConfig
from mashumaro.types import Discriminator
from rich.table import Table

from .catalog import Link, WebImage
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
    INLINE_HERO = "inlineHero"
    LANDSCAPE = "landscape"
    LANDSCAPE_LOGO = "landscapeLogo"
    SIMPLE = "simple"
    SQUARED = "squared"
    SQUARED_LOGO = "squaredLogo"
    NYHETS_ATOM = "nyhetsAtom"
    RADIO_MULTI_HERO = "radioMultiHero"
    SIDEKICK_LOGO = "sidekickLogo"


class PlaceholderType(StrEnum):
    CATEGORY_PERSONALISED_RECOMMENDATIONS = "categoryPersonalisedRecommendations"


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
    type: PlaceholderType | None = None
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
class EpisodeLinks(BaseDataClassORJSONMixin):
    program: Link
    series: Link
    playback_metadata: Link = field(metadata=field_options(alias="playbackMetadata"))
    playback_manifest: Link = field(metadata=field_options(alias="playbackManifest"))
    favourite: Link
    share: Link


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
class PodcastLinks(BaseDataClassORJSONMixin):
    podcast: Link
    share: Link
    favourite: TemplatedLink | None = None


@dataclass
class PodcastEpisodeLinks(BaseDataClassORJSONMixin):
    podcast_episode: Link = field(metadata=field_options(alias="podcastEpisode"))
    podcast: Link
    audio_download: Link = field(metadata=field_options(alias="audioDownload"))
    share: Link
    playback_metadata: Link = field(metadata=field_options(alias="playbackMetadata"))
    playback_manifest: Link = field(metadata=field_options(alias="playbackManifest"))
    favourite: TemplatedLink | None = None


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
    id: str
    image: WebImage
    backdrop_image: WebImage | None = field(default=None, metadata=field_options(alias="backdropImage"))
    title: str | None = None
    tagline: str | None = None
    accessibility_label: str | None = field(default=None, metadata=field_options(alias="accessibilityLabel"))

    class Config(BaseConfig):
        discriminator = Discriminator(
            field="type",
            include_subtypes=True,
        )


@dataclass
class Section(BaseDataClassORJSONMixin):
    id: str
    e_commerce: SectionEcommerce | None = field(default=None, metadata=field_options(alias="eCommerce"))

    class Config(BaseConfig):
        discriminator = Discriminator(
            field="type",
            include_subtypes=True,
        )


@dataclass(kw_only=True)
class PlaceholderSection(Section):
    type = SectionType.PLACEHOLDER
    placeholder: Placeholder


@dataclass
class PluggedEpisode(BaseDataClassORJSONMixin):
    program_id: str = field(metadata=field_options(alias="programId"))
    series_id: str = field(metadata=field_options(alias="seriesId"))
    series_title: str = field(metadata=field_options(alias="seriesTitle"))
    episode_title: str = field(metadata=field_options(alias="episodeTitle"))
    duration: timedelta = field(
        metadata=field_options(deserialize=parse_duration, serialize=duration_isoformat)
    )
    _links: EpisodeLinks


@dataclass
class PluggedSeries(BaseDataClassORJSONMixin):
    series_id: str = field(metadata=field_options(alias="seriesId"))
    series_title: str = field(metadata=field_options(alias="seriesTitle"))
    _links: SeriesLinks
    image: WebImage | None = None
    number_of_episodes: int | None = field(default=None, metadata=field_options(alias="numberOfEpisodes"))


@dataclass
class PluggedChannel(BaseDataClassORJSONMixin):
    channel_id: str = field(metadata=field_options(alias="channelId"))
    channel_title: str = field(metadata=field_options(alias="channelTitle"))
    show_live_badge: bool = field(metadata=field_options(alias="showLiveBadge"))
    _links: ChannelLinks


@dataclass
class PluggedStandaloneProgram(BaseDataClassORJSONMixin):
    program_id: str = field(metadata=field_options(alias="programId"))
    program_title: str = field(metadata=field_options(alias="programTitle"))
    duration: timedelta = field(
        metadata=field_options(deserialize=parse_duration, serialize=duration_isoformat)
    )
    _links: StandaloneProgramLinks


@dataclass
class PluggedPodcast(BaseDataClassORJSONMixin):
    podcast_id: str = field(metadata=field_options(alias="podcastId"))
    podcast_title: str = field(metadata=field_options(alias="podcastTitle"))
    _links: PodcastLinks
    image_url: str | None = field(default=None, metadata=field_options(alias="imageUrl"))
    number_of_episodes: int | None = field(default=None, metadata=field_options(alias="numberOfEpisodes"))


@dataclass
class PluggedPodcastEpisode(BaseDataClassORJSONMixin):
    episode_id: str = field(metadata=field_options(alias="episodeId"))
    podcast_id: str = field(metadata=field_options(alias="podcastId"))
    podcast_title: str = field(metadata=field_options(alias="podcastTitle"))
    podcast_episode_title: str = field(metadata=field_options(alias="podcastEpisodeTitle"))
    duration: timedelta = field(
        metadata=field_options(deserialize=parse_duration, serialize=duration_isoformat)
    )
    image_url: str = field(metadata=field_options(alias="imageUrl"))
    _links: PodcastEpisodeLinks
    podcast: PluggedPodcast | None = None


@dataclass
class PluggedPodcastSeason(BaseDataClassORJSONMixin):
    _links: PodcastSeasonLinks
    podcast_id: str = field(metadata=field_options(alias="podcastId"))
    season_id: str = field(metadata=field_options(alias="seasonId"))
    season_number: int = field(metadata=field_options(alias="seasonNumber"))
    number_of_episodes: int = field(metadata=field_options(alias="numberOfEpisodes"))
    image_url: str = field(metadata=field_options(alias="imageUrl"))
    podcast_title: str = field(metadata=field_options(alias="podcastTitle"))
    podcast_season_title: str = field(metadata=field_options(alias="podcastSeasonTitle"))


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


@dataclass(kw_only=True)
class ChannelPlug(Plug):
    type = PlugType.CHANNEL
    channel: PluggedChannel

    # noinspection PyUnusedLocal
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.type}[/b]"
        table = Table("Attribute", "Value")
        table.add_row("id", self.id)
        table.add_row("channel.title", self.channel.channel_title)
        yield table


@dataclass(kw_only=True)
class SeriesPlug(Plug):
    type = PlugType.SERIES
    series: PluggedSeries

    # noinspection PyUnusedLocal
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.type}[/b]"
        table = Table("Attribute", "Value")
        table.add_row("id", self.id)
        table.add_row("series.title", self.series.series_title)
        table.add_row("series.id", self.series.series_id)
        table.add_row("series.number_of_episodes", str(self.series.number_of_episodes))
        yield table


@dataclass(kw_only=True)
class EpisodePlug(Plug):
    type = PlugType.EPISODE
    episode: PluggedEpisode

    # noinspection PyUnusedLocal
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.type}[/b]"
        table = Table("Attribute", "Value")
        table.add_row("id", self.id)
        table.add_row("episode.title", self.episode.episode_title)
        yield table


@dataclass(kw_only=True)
class StandaloneProgramPlug(Plug):
    type = PlugType.STANDALONE_PROGRAM
    standalone_program: PluggedStandaloneProgram = field(metadata=field_options(alias="standaloneProgram"))

    # noinspection PyUnusedLocal
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.type}[/b]"
        table = Table("Attribute", "Value")
        table.add_row("id", self.id)
        table.add_row("program.title", self.standalone_program.program_title)
        table.add_row("program.duration", str(self.standalone_program.duration))
        yield table


@dataclass(kw_only=True)
class PodcastPlug(Plug):
    type = PlugType.PODCAST
    podcast: PluggedPodcast

    # noinspection PyUnusedLocal
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.type}[/b]"
        table = Table("Attribute", "Value")
        table.add_row("id", self.id)
        table.add_row("podcast.podcast_id", self.podcast.podcast_id)
        table.add_row("podcast.podcast_title", self.podcast.podcast_title)
        table.add_row("podcast.number_of_episodes", str(self.podcast.number_of_episodes))
        yield table


@dataclass(kw_only=True)
class PodcastEpisodePlug(Plug):
    type = PlugType.PODCAST_EPISODE
    podcast_episode: PluggedPodcastEpisode = field(metadata=field_options(alias="podcastEpisode"))

    # noinspection PyUnusedLocal
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.type}[/b]"
        table = Table("Attribute", "Value")
        table.add_row("id", self.id)
        table.add_row("podcast_id", self.podcast_episode.podcast_id)
        table.add_row("podcast_episode.title", self.podcast_episode.podcast_episode_title)
        yield table


@dataclass(kw_only=True)
class PodcastSeasonPlug(Plug):
    type = PlugType.PODCAST_SEASON
    podcast_season: PluggedPodcastSeason = field(metadata=field_options(alias="podcastSeason"))
    description: str | None = None

    # noinspection PyUnusedLocal
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.type}[/b]"
        table = Table("Attribute", "Value")
        table.add_row("id", self.id)
        table.add_row("podcast_season.podcast_id", self.podcast_season.podcast_id)
        table.add_row("podcast_season.season_id", self.podcast_season.season_id)
        table.add_row("podcast_season.season_number", str(self.podcast_season.season_number))
        table.add_row("podcast_season.number_of_episodes", str(self.podcast_season.number_of_episodes))
        table.add_row("podcast_season.image_url", self.podcast_season.image_url)
        table.add_row("podcast_season.podcast_title", self.podcast_season.podcast_title)
        table.add_row("podcast_season.podcast_season_title", self.podcast_season.podcast_season_title)
        yield table


@dataclass(kw_only=True)
class LinkPlug(Plug):
    type = PlugType.LINK
    link: LinkPlugInner

    # noinspection PyUnusedLocal
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.type}[/b]"
        table = Table("Attribute", "Value")
        table.add_row("id", self.id)
        table.add_row("link", str(self.link))
        yield table


@dataclass(kw_only=True)
class PagePlug(Plug):
    type = PlugType.PAGE
    page: PagePlugInner
    description: str | None = None

    # noinspection PyUnusedLocal
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.type}[/b]"
        table = Table("Attribute", "Value")
        table.add_row("id", self.id)
        table.add_row("page", str(self.page))
        yield table


@dataclass
class Included(BaseDataClassORJSONMixin):
    title: str
    plugs: list[Plug]
    count: int
    display_contract: DisplayContract | None = field(
        default=None, metadata=field_options(alias="displayContract")
    )
    plug_size: PlugSize | None = field(default=None, metadata=field_options(alias="plugSize"))


@dataclass(kw_only=True)
class IncludedSection(Section):
    type = SectionType.INCLUDED
    included: Included


@dataclass
class Page(BaseDataClassORJSONMixin):
    id: str
    title: str
    published_time: datetime = field(metadata=field_options(alias="publishedTime"))
    sections: list[Section]
    _links: PageLinks
    page_version: str | None = field(default=None, metadata=field_options(alias="pageVersion"))
    display_type: DisplayType | None = field(default=None, metadata=field_options(alias="displayType"))
    image: WebImage | None = None
    image_square: WebImage | None = field(default=None, metadata=field_options(alias="imageSquare"))
    buttons: list[ButtonItem] | None = None
    back_button: ButtonItem | None = field(default=None, metadata=field_options(alias="backButton"))


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
