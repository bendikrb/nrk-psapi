from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from mashumaro import field_options
from mashumaro.config import BaseConfig
from mashumaro.mixins.orjson import DataClassORJSONMixin
from mashumaro.types import Discriminator


class DisplayType(str, Enum):
    DEFAULT = 'default'
    GRID = 'grid'

    def __str__(self) -> str:
        return str(self.value)


class DisplayContract(str, Enum):
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

    def __str__(self) -> str:
        return str(self.value)


class PlugSize(str, Enum):
    SMALL = 'small'
    MEDIUM = 'medium'
    LARGE = 'large'

    def __str__(self) -> str:
        return str(self.value)


class PageTypeEnum(str, Enum):
    CATEGORY = 'category'
    SUBCATEGORY = 'subcategory'

    def __str__(self) -> str:
        return str(self.value)

@dataclass
class BaseDataClassORJSONMixin(DataClassORJSONMixin):
    class Config(BaseConfig):
        omit_none = True
        allow_deserialization_not_by_alias = True


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
class SimpleLink(BaseDataClassORJSONMixin):
    href: str


@dataclass
class HalLink(BaseDataClassORJSONMixin):
    href: str


@dataclass
class TemplatedLink(BaseDataClassORJSONMixin):
    href: str
    templated: Literal[True] | None


@dataclass
class WebImage(BaseDataClassORJSONMixin):
    uri: str
    width: int


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
    program: HalLink
    playback_metadata: HalLink
    playback_manifest: HalLink
    share: HalLink


@dataclass
class PageListItemLinks(BaseDataClassORJSONMixin):
    self: SimpleLink


@dataclass
class EpisodeLinks(BaseDataClassORJSONMixin):
    program: HalLink
    series: HalLink
    playback_metadata: HalLink
    playback_manifest: HalLink
    share: HalLink
    favourite: TemplatedLink | None = None


@dataclass
class PageLinks(BaseDataClassORJSONMixin):
    self: HalLink


@dataclass
class SeriesLinks(BaseDataClassORJSONMixin):
    series: HalLink
    share: HalLink
    favourite: TemplatedLink | None = None


@dataclass
class ChannelLinks(BaseDataClassORJSONMixin):
    playback_metadata: HalLink
    playback_manifest: HalLink
    share: HalLink


@dataclass
class PodcastEpisodeLinks(BaseDataClassORJSONMixin):
    podcast_episode: HalLink | str | None = field(default=None, metadata=field_options(alias="podcastEpisode"))
    podcast: HalLink | str | None = None
    audio_download: HalLink | str | None = field(default=None, metadata=field_options(alias="audioDownload"))
    share: HalLink | str | None = None
    playback_metadata: HalLink | str | None = field(default=None, metadata=field_options(alias="playbackMetadata"))
    playback_manifest: HalLink | str | None = field(default=None, metadata=field_options(alias="playbackManifest"))
    favourite: TemplatedLink | str | None = None


@dataclass
class PodcastSeasonLinks(BaseDataClassORJSONMixin):
    podcast_season: HalLink
    podcast: HalLink
    share: HalLink
    favourite: TemplatedLink | None = None


@dataclass
class LinkPlugLinks(BaseDataClassORJSONMixin):
    external_url: HalLink


@dataclass
class PagePlugLinks(BaseDataClassORJSONMixin):
    page_url: HalLink


@dataclass
class PodcastLinks(BaseDataClassORJSONMixin):
    podcast: HalLink | str | None = None
    share: HalLink | str | None = None
    favourite: TemplatedLink | str | None = None


@dataclass
class HalLinks(BaseDataClassORJSONMixin):
    self: SimpleLink


@dataclass
class Image(BaseDataClassORJSONMixin):
    id: str
    web_images: list[WebImage] = field(metadata=field_options(alias="webImages"))


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
    type = "placeholder"
    placeholder: Placeholder
    id: str | None = None
    e_commerce: SectionEcommerce | None = field(default=None, metadata=field_options(alias="eCommerce"))


@dataclass
class Episode(BaseDataClassORJSONMixin):
    _links: EpisodeLinks
    duration: str
    program_id: str | None = field(metadata=field_options(alias="programId"))
    series_id: str | None = field(metadata=field_options(alias="seriesId"))
    start_time: str | None = field(default=None, metadata=field_options(alias="startTime"))
    series_title: str | None = field(default=None, metadata=field_options(alias="seriesTitle"))
    episode_title: str | None = field(default=None, metadata=field_options(alias="episodeTitle"))


@dataclass
class Series(BaseDataClassORJSONMixin):
    _links: SeriesLinks
    series_id: str | None = field(default=None, metadata=field_options(alias="seriesId"))
    series_title: str | None = field(default=None, metadata=field_options(alias="seriesTitle"))


@dataclass
class Channel(BaseDataClassORJSONMixin):
    _links: ChannelLinks
    channel_id: str | None = field(default=None, metadata=field_options(alias="channelId"))
    show_live_badge: bool | None = field(default=None, metadata=field_options(alias="showLiveBadge"))
    channel_title: str | None = field(default=None, metadata=field_options(alias="channelTitle"))
    start_date_time: str | None = field(default=None, metadata=field_options(alias="startDateTime"))


@dataclass
class StandaloneProgram(BaseDataClassORJSONMixin):
    _links: StandaloneProgramLinks
    duration: str
    program_id: str | None = field(default=None, metadata=field_options(alias="programId"))
    start_time: str | None = field(default=None, metadata=field_options(alias="startTime"))
    program_title: str | None = field(default=None, metadata=field_options(alias="programTitle"))


@dataclass
class Titles(BaseDataClassORJSONMixin):
    title: str
    subtitle: str


@dataclass
class Podcast(BaseDataClassORJSONMixin):
    _links: PodcastLinks | None = None
    podcast_id: str | None = field(default=None, metadata=field_options(alias="podcastId"))
    image_url: str | None = field(default=None, metadata=field_options(alias="imageUrl"))
    number_of_episodes: int | None = field(default=None, metadata=field_options(alias="numberOfEpisodes"))
    # podcast_title: str | None = field(default=None, metadata=field_options(alias="podcastTitle"))
    titles: Titles | None = None

    @property
    def podcast_title(self):
        return self.titles.title


@dataclass
class PodcastEpisode(BaseDataClassORJSONMixin):
    titles: Titles | None = None
    _links: PodcastEpisodeLinks | None = None
    duration: str | None = None
    image_url: str | None = field(default=None, metadata=field_options(alias="imageUrl"))
    podcast_id: str | None = field(default=None, metadata=field_options(alias="podcastId"))
    episode_id: str | None = field(default=None, metadata=field_options(alias="episodeId"))
    start_time: str | None = field(default=None, metadata=field_options(alias="startTime"))
    podcast_title: str | None = field(default=None, metadata=field_options(alias="podcastTitle"))
    podcast_episode_title: str | None = field(default=None, metadata=field_options(alias="podcastEpisodeTitle"))
    podcast: Podcast | None = None


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
    image: Image | None = None
    image_square: Image | None = field(default=None, metadata=field_options(alias="imageSquare"))


@dataclass
class Pages(BaseDataClassORJSONMixin):
    _links: HalLinks
    pages: list[PageListItem]


@dataclass
class ChannelPlug(Plug):
    type = "channel"
    channel: Channel
    id: str | None = None
    image: Image | None = None
    e_commerce: PlugEcommerce | None = field(default=None, metadata=field_options(alias="eCommerce"))
    analytics: PlugAnalytics | None = None
    title: str | None = None
    tagline: str | None = None
    description: str | None = None
    accessibility_label: str | None = field(default=None, metadata=field_options(alias="accessibilityLabel"))
    backdrop_image: Image | None = field(default=None, metadata=field_options(alias="backdropImage"))


@dataclass
class SeriesPlug(Plug):
    type = "series"
    series: Series
    id: str | None = None
    image: Image | None = None
    e_commerce: PlugEcommerce | None = field(default=None, metadata=field_options(alias="eCommerce"))
    analytics: PlugAnalytics | None = None
    title: str | None = None
    tagline: str | None = None
    description: str | None = None
    accessibility_label: str | None = field(default=None, metadata=field_options(alias="accessibilityLabel"))
    backdrop_image: Image | None = field(default=None, metadata=field_options(alias="backdropImage"))


@dataclass
class EpisodePlug(Plug):
    type = "episode"
    episode: Episode
    id: str | None = None
    image: Image | None = None
    e_commerce: PlugEcommerce | None = field(default=None, metadata=field_options(alias="eCommerce"))
    analytics: PlugAnalytics | None = None
    title: str | None = None
    tagline: str | None = None
    description: str | None = None
    accessibility_label: str | None = field(default=None, metadata=field_options(alias="accessibilityLabel"))
    backdrop_image: Image | None = field(default=None, metadata=field_options(alias="backdropImage"))


@dataclass
class StandaloneProgramPlug(Plug):
    type = "standaloneProgram"
    standalone_program: StandaloneProgram = field(metadata=field_options(alias="standaloneProgram"))
    hid: str | None = None
    image: Image | None = None
    e_commerce: PlugEcommerce | None = field(default=None, metadata=field_options(alias="eCommerce"))
    analytics: PlugAnalytics | None = None
    title: str | None = None
    tagline: str | None = None
    description: str | None = None
    accessibility_label: str | None = field(default=None, metadata=field_options(alias="accessibilityLabel"))
    backdrop_image: Image | None = field(default=None, metadata=field_options(alias="backdropImage"))


@dataclass
class PodcastPlug(Plug):
    type = "podcast"
    podcast: Podcast
    _links: PodcastLinks
    # id: str | None = None
    image: Image | None = None
    e_commerce: PlugEcommerce | None = field(default=None, metadata=field_options(alias="eCommerce"))
    analytics: PlugAnalytics | None = None
    # title: str | None = None
    # tagline: str | None = None
    description: str | None = None
    accessibility_label: str | None = field(default=None, metadata=field_options(alias="accessibilityLabel"))
    backdrop_image: Image | None = field(default=None, metadata=field_options(alias="backdropImage"))

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


@dataclass
class PodcastEpisodePlug(Plug):
    type = "podcastEpisode"
    podcast_episode: PodcastEpisode = field(metadata=field_options(alias="podcastEpisode"))
    _links: PodcastEpisodeLinks
    id: str | None = None
    image: Image | None = None
    e_commerce: PlugEcommerce | None = field(default=None, metadata=field_options(alias="eCommerce"))
    analytics: PlugAnalytics | None = None
    title: str | None = None
    tagline: str | None = None
    description: str | None = None
    accessibility_label: str | None = field(default=None, metadata=field_options(alias="accessibilityLabel"))
    backdrop_image: Image | None = field(default=None, metadata=field_options(alias="backdropImage"))

    @property
    def links(self):
        return self._links


@dataclass
class PodcastSeasonPlug(Plug):
    type = "podcastSeason"
    id: str
    podcast_season: PodcastSeason = field(metadata=field_options(alias="podcastSeason"))
    image: Image | None = None
    e_commerce: PlugEcommerce | None = field(default=None, metadata=field_options(alias="eCommerce"))
    analytics: PlugAnalytics | None = None
    title: str | None = None
    tagline: str | None = None
    description: str | None = None
    accessibility_label: str | None = field(default=None, metadata=field_options(alias="accessibilityLabel"))
    backdrop_image: Image | None = field(default=None, metadata=field_options(alias="backdropImage"))


@dataclass
class LinkPlug(Plug):
    type = "link"
    link: LinkPlugInner
    id: str | None = None
    image: Image | None = None
    e_commerce: PlugEcommerce | None = field(default=None, metadata=field_options(alias="eCommerce"))
    analytics: PlugAnalytics | None = None
    title: str | None = None
    tagline: str | None = None
    description: str | None = None
    accessibility_label: str | None = field(default=None, metadata=field_options(alias="accessibilityLabel"))
    backdrop_image: Image | None = field(default=None, metadata=field_options(alias="backdropImage"))


@dataclass
class PagePlug(Plug):
    type = "page"
    page: PagePlugInner
    id: str | None = None
    image: Image | None = None
    e_commerce: PlugEcommerce | None = field(default=None, metadata=field_options(alias="eCommerce"))
    analytics: PlugAnalytics | None = None
    title: str | None = None
    tagline: str | None = None
    description: str | None = None
    accessibility_label: str | None = field(default=None, metadata=field_options(alias="accessibilityLabel"))
    backdrop_image: Image | None = field(default=None, metadata=field_options(alias="backdropImage"))


@dataclass
class Included(BaseDataClassORJSONMixin):
    plugs: list[Plug]
    count: int | None = None
    display_contract: DisplayContract | None = field(default=None, metadata=field_options(alias="displayContract"))
    plug_size: PlugSize | None = field(default=None, metadata=field_options(alias="plugSize"))
    title: str | None = None


@dataclass
class IncludedSection(Section):
    type = "included"
    included: Included
    id: str | None = None
    e_commerce: SectionEcommerce | None = field(default=None, metadata=field_options(alias="eCommerce"))


@dataclass
class Page(BaseDataClassORJSONMixin):
    title: str
    sections: list[Section]
    _links: PageLinks
    id: str | None = None
    buttons: list[ButtonItem] | None = None
    display_type: DisplayType | None = field(default=None, metadata=field_options(alias="displayType"))
    published_time: str | None = field(default=None, metadata=field_options(alias="publishedTime"))
    user_segment: str | None = field(default=None, metadata=field_options(alias="userSegment"))
    image: Image | None = field(default=None, metadata=field_options(alias="image"))
    image_square: Image | None = field(default=None, metadata=field_options(alias="imageSquare"))
    experiment_id: str | None = field(default=None, metadata=field_options(alias="experimentId"))
    variant: int | None = field(default=None, metadata=field_options(alias="variant"))
    e_commerce: PageEcommerce | None = field(default=None, metadata=field_options(alias="eCommerce"))
    page_version: str | None = field(default=None, metadata=field_options(alias="pageVersion"))
    recommendation_id: str | None = field(default=None, metadata=field_options(alias="recommendationId"))
    back_button: ButtonItem | None = field(default=None, metadata=field_options(alias="backButton"))


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
