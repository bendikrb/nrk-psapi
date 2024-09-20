from __future__ import annotations

from dataclasses import dataclass

from rfeed import ElementRequiredError, Extension, Serializable


class Podcast(Extension):
    """Extension for Podcast Index metatags.
    More information at https://podcastindex.org/namespace/1.0.
    """

    def __init__(self, guid=None, license=None, locked=None, people=None, images=None):  # noqa: A002
        Extension.__init__(self)

        self.guid = guid
        self.license = license
        self.locked = locked
        self.people = [] if people is None else people
        self.images = [] if images is None else images

        if isinstance(self.people, PodcastPerson):
            self.people = [self.people]
        elif isinstance(self.people, str):
            self.people = [PodcastPerson(self.people)]

    def get_namespace(self):
        return {
            "xmlns:podcast": "https://podcastindex.org/namespace/1.0",
            "version": "2.0",
        }

    def publish(self, handler):
        Extension.publish(self, handler)

        if self.guid is not None:
            self._write_element("podcast:guid", self.guid)

        if self.license is not None:
            self._write_element("podcast:license", self.license)

        if self.locked is not None:
            self._write_element("podcast:locked", self.locked)

        for person in self.people:
            if isinstance(person, str):
                person = PodcastPerson(person)  # noqa: PLW2901
            person.publish(self.handler)


class PodcastPerson(Serializable):
    """Extension for Podcast Index Person metatags.
    More information at https://podcastindex.org/namespace/1.0#person.
    """

    def __init__(self, name: str, role=None, group=None, img=None, href=None):
        Serializable.__init__(self)

        if name is None:
            raise ElementRequiredError("name")

        self.name = name
        self.role = role
        self.group = group
        self.img = img
        self.href = href

    def publish(self, handler):
        Serializable.publish(self, handler)

        attrs = {}
        if self.role is not None:
            attrs["role"] = self.role
        if self.group is not None:
            attrs["group"] = self.group
        if self.img is not None:
            attrs["img"] = self.img
        if self.href is not None:
            attrs["href"] = self.href

        self._write_element("podcast:person", self.name, attrs)


@dataclass
class PodcastImagesImage:
    url: str
    width: int


class PodcastImages(Serializable):
    """Extension for Podcast Index Images metatags.
    More information at https://podcastindex.org/namespace/1.0#images.
    """

    def __init__(self, images: list[PodcastImagesImage]):
        Serializable.__init__(self)

        if images is None:
            raise ElementRequiredError("images")

        self.images = images

    def publish(self, handler):
        Serializable.publish(self, handler)

        attrs = {
            "srcset": ", ".join(f"{image.url} {image.width}w" for image in self.images),
        }
        self._write_element("podcast:images", None, attrs)


class PodcastSeason(Serializable):
    """Extension for Podcast Index Season metatags.
    More information at https://podcastindex.org/namespace/1.0#season.
    """

    def __init__(self, number: int, name=None):
        Serializable.__init__(self)

        if number is None:
            raise ElementRequiredError("number")

        self.number = number
        self.name = name

    def publish(self, handler):
        Serializable.publish(self, handler)

        attrs = {}
        if self.name is not None:
            attrs["name"] = self.name

        self._write_element("podcast:season", self.number, attrs)


class PodcastEpisode(Serializable):
    """Extension for Podcast Index Episode metatags.
    More information at https://podcastindex.org/namespace/1.0#episode.
    """

    def __init__(self, number: float, display=None):
        Serializable.__init__(self)

        if number is None:
            raise ElementRequiredError("number")

        self.number = number
        self.display = display

    def publish(self, handler):
        Serializable.publish(self, handler)

        attrs = {}
        if self.display is not None:
            attrs["display"] = self.display

        self._write_element("podcast:episode", self.number, attrs)


class PodcastChapters(Serializable):
    """Extension for Podcast Index Chapter metatags.
    More information at https://podcastindex.org/namespace/1.0#chapters.
    """

    def __init__(self, url=None, type_=None):
        Serializable.__init__(self)

        if url is None:
            raise ElementRequiredError("url")
        if type_ is None:
            raise ElementRequiredError("type")

        self.url = url
        self.type = type_

    def publish(self, handler):
        Serializable.publish(self, handler)

        self._write_element("podcast:chapters", None, {"url": self.url, "type": self.type})


class PodcastTranscript(Serializable):
    """Extension for Podcast Index Transcript metatags.
    More information at https://podcastindex.org/namespace/1.0#transcript.
    """

    def __init__(self, url: str, type_: str, language=None, rel=None):
        Serializable.__init__(self)

        if url is None:
            raise ElementRequiredError("url")
        if type_ is None:
            raise ElementRequiredError("type")

        self.url = url
        self.type = type_
        self.language = language
        self.rel = rel

    def publish(self, handler):
        Serializable.publish(self, handler)

        attrs = {
            "url": self.url,
            "type": self.type,
        }
        if self.language is not None:
            attrs["language"] = self.language
        if self.rel is not None:
            attrs["rel"] = self.rel

        self._write_element("podcast:transcript", None, attrs)
