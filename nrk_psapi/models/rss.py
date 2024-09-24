from __future__ import annotations

from typing import NotRequired, TypedDict


class EpisodeChapter(TypedDict):
    startTime: float
    title: NotRequired[str]
    img: NotRequired[str]
    url: NotRequired[str]
    toc: NotRequired[bool]
    endTime: NotRequired[float]
    location: NotRequired[dict]
