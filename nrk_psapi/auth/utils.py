from __future__ import annotations

from html.parser import HTMLParser
from typing import TYPE_CHECKING

import orjson

from nrk_psapi.auth.models import LoginFlowState

if TYPE_CHECKING:
    from nrk_psapi.auth.models import HashingAlgorithm


class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.form_data = {}
        self.current_script = None
        self.model_json = None

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            attr_dict = dict(attrs)
            if (
                "type" in attr_dict
                and attr_dict["type"] == "hidden"
                and "name" in attr_dict
                and "value" in attr_dict
            ):
                self.form_data[attr_dict["name"]] = attr_dict["value"]
        elif tag == "script":
            attr_dict = dict(attrs)
            if attr_dict.get("id") == "model" and attr_dict.get("type") == "application/json":
                self.current_script = "model"

    def handle_data(self, data):
        if self.current_script == "model":
            self.model_json = orjson.loads(data)

    def handle_endtag(self, tag):
        if tag == "script":
            self.current_script = None


def parse_html_auth_form(html_content) -> LoginFlowState:
    parser = FormParser()
    parser.feed(html_content)
    data = parser.form_data
    data["model"] = parser.model_json
    return LoginFlowState.from_dict(data)


def get_n(log_n):
    """Get 2^logN."""
    return (1 << log_n) & 0xFFFFFFFF


def parse_hashing_algorithm(algorithm: str | None) -> HashingAlgorithm:
    """Parse hashing algorithm string, like 'cscrypt:17:8:1:32'."""
    default_algorithm = {"algorithm": "cleartext"}
    if algorithm is None:
        return default_algorithm
    if "cscrypt" not in algorithm:
        return default_algorithm
    parts = algorithm.split(":")
    if len(parts) < 5:  # noqa: PLR2004
        return default_algorithm

    return {
        "algorithm": "cscrypt",
        "n": get_n(int(parts[1])),
        "r": int(parts[2]),
        "p": int(parts[3]),
        "dkLen": int(parts[4]),
    }
