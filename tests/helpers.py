from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

from aiohttp.web_response import json_response
from aresponses import ResponsesMockServer
from aresponses.main import Route

# noinspection PyProtectedMember
from aresponses.utils import ANY, _text_matches_pattern
import orjson
from yarl import URL

from nrk_psapi.auth.auth import OAUTH_AUTH_BASE_URL, OAUTH_LOGIN_BASE_URL

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def save_fixture(name: str, data: dict):  # pragma: no cover
    """Save API response data to a fixture file."""
    file_path = FIXTURE_DIR / f"{name}.json"
    with open(file_path, "w") as f:
        f.write(orjson.dumps(data))


def load_fixture(name: str) -> str:
    """Load a fixture."""
    path = FIXTURE_DIR / f"{name}.json"
    if not path.exists():  # pragma: no cover
        raise FileNotFoundError(f"Fixture {name} not found")
    return path.read_text(encoding="utf-8")


def load_fixture_json(name: str) -> dict:
    """Load a fixture as JSON."""
    data = load_fixture(name)
    return orjson.loads(data)


class CustomRoute(Route):  # pragma: no cover
    """Custom route for aresponses."""

    def __init__(
        self,
        method_pattern=ANY,
        host_pattern=ANY,
        path_pattern=ANY,
        path_qs=None,
        body_pattern=ANY,
        match_querystring=False,
        repeat=1,
    ):
        super().__init__(method_pattern, host_pattern, path_pattern, body_pattern, match_querystring, repeat)
        if path_qs is not None:
            self.path_qs = urlencode(path_qs)
            self.match_querystring = True

    async def matches(self, request):
        path_to_match = urlparse(request.path_qs)
        query_to_match = parse_qs(path_to_match.query)
        parsed_path = urlparse(self.path_pattern)
        parsed_query = parse_qs(self.path_qs) if self.path_qs else parse_qs(parsed_path.query)

        if not _text_matches_pattern(self.host_pattern, request.host):
            return False

        if parsed_path.path != path_to_match.path:
            return False

        if self.match_querystring and query_to_match != parsed_query:
            return False

        if not _text_matches_pattern(self.method_pattern.lower(), request.method.lower()):  # noqa: SIM103
            return False

        return True


def setup_auth_mocks(aresponses: ResponsesMockServer):
    aresponses.add(
        URL(OAUTH_LOGIN_BASE_URL).host,
        "/auth/web/login",
        "GET",
        aresponses.Response(
            status=302,
            headers={
                "Location": "https://innlogging.nrk.no/connect/authorize?scope=openid+&response_type=code&client_id=radio.nrk.no.web&redirect_uri=https%3A%2F%2Fradio.nrk.no%2Fauth%2FsignInCallback&state=N7zlfSU&code_challenge=vq&code_challenge_method=S256&acr_values=encodedExitUrl%3Dhttps%253A%252F%252Fradio.nrk.no%252Fmittinnhold",
            },
        ),
        repeat=float("inf"),
    )
    aresponses.add(
        URL(OAUTH_AUTH_BASE_URL).host,
        "/connect/authorize",
        "GET",
        aresponses.Response(
            status=302,
            headers={
                "Location": "/logginn?returnUrl=%2Fconnect%2Fauthorize%2Fcallback%3Fscope%3Dopenid",
            },
        ),
        repeat=float("inf"),
    )
    aresponses.add(
        URL(OAUTH_AUTH_BASE_URL).host,
        "/logginn",
        "GET",
        aresponses.Response(body="OK", content_type="text/html"),
        repeat=float("inf"),
    )

    aresponses.add(
        URL(OAUTH_AUTH_BASE_URL).host,
        "/getHashingInstructions",
        "POST",
        json_response(data=load_fixture_json("auth_hashing_instructions")),
        repeat=float("inf"),
    )

    aresponses.add(
        URL(OAUTH_AUTH_BASE_URL).host,
        "/logginn",
        "POST",
        json_response(data={"firstName": "Userus"}),
        repeat=float("inf"),
    )

    aresponses.add(
        URL(OAUTH_AUTH_BASE_URL).host,
        "/connect/authorize/callback",
        "GET",
        aresponses.Response(
            status=302,
            headers={
                "Location": "https://radio.nrk.no/auth/signInCallback?code=SVLdG1qB1iW7-KlJAYEBabfT",
            },
        ),
        repeat=float("inf"),
    )
    aresponses.add(
        URL(OAUTH_LOGIN_BASE_URL).host,
        "/auth/signInCallback",
        "GET",
        aresponses.Response(
            status=302,
            headers={
                "Location": "https://radio.nrk.no/mittinnhold",
            },
        ),
        repeat=float("inf"),
    )
    aresponses.add(
        URL(OAUTH_LOGIN_BASE_URL).host,
        "/mittinnhold",
        "GET",
        aresponses.Response(body="OK", content_type="text/html"),
        repeat=float("inf"),
    )

    aresponses.add(
        URL(OAUTH_LOGIN_BASE_URL).host,
        "/auth/session/tokenforsub/_",
        "POST",
        json_response(data=load_fixture_json("auth_token")),
        repeat=float("inf"),
    )
