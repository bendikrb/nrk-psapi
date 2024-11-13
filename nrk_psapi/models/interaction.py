from __future__ import annotations

from dataclasses import dataclass, field

from mashumaro import field_options

from .common import BaseDataClassORJSONMixin


@dataclass
class RadioMessage(BaseDataClassORJSONMixin):
    accept_terms: bool = field(metadata=field_options(alias="acceptTerms"))
    anonymous: bool
    message: str
    phone: str | None = None
