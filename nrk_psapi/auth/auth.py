from __future__ import annotations

from asyncio import TimeoutError
from dataclasses import dataclass, field
from urllib.parse import quote_plus

from aiohttp.client import ClientError, ClientResponseError, ClientSession
import scrypt
from yarl import URL

from nrk_psapi.auth.models import HashingInstructions, NrkAuthData, NrkUserCredentials
from nrk_psapi.auth.utils import parse_hashing_algorithm
from nrk_psapi.const import LOGGER as _LOGGER
from nrk_psapi.exceptions import NrkPsApiAuthenticationError, NrkPsApiConnectionTimeoutError

OAUTH_LOGIN_BASE_URL = "https://radio.nrk.no"
OAUTH_AUTH_BASE_URL = "https://innlogging.nrk.no"
OAUTH_RETURN_URL = "https://radio.nrk.no/mittinnhold"
OAUTH_CLIENT_ID = "radio.nrk.no.web"


@dataclass
class NrkAuthClient:
    user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"

    request_timeout: int = 15
    session: ClientSession | None = None

    user_credentials: NrkUserCredentials | None = None

    _credentials: NrkAuthData | None = field(default=None, init=False)
    _close_session: bool = False

    def get_credentials(self) -> dict | None:
        """Get the current credentials as a dictionary, or None if not set."""
        if self._credentials is not None:
            return self._credentials.to_dict()
        return None  # pragma: no cover

    def set_credentials(self, credentials: NrkAuthData | dict | str):
        """Set the credentials.

        Args:
            credentials (NrkAuthData | dict | str): The credentials to set.

        """
        if isinstance(credentials, NrkAuthData):
            self._credentials = credentials
        elif isinstance(credentials, dict):
            self._credentials = NrkAuthData.from_dict(credentials)
        else:
            self._credentials = NrkAuthData.from_json(credentials)

    async def async_get_access_token(self) -> str:
        """Get access token."""
        if self._credentials is None:
            raise NrkPsApiAuthenticationError("No credentials set")
        # TODO(@bendikrb): Check if token is still valid, implement refresh logic
        return self._credentials.session.access_token

    @property
    def request_header(self) -> dict[str, str]:
        """Generate a header for HTTP requests to the server."""
        return {
            "user-agent": self.user_agent,
        }

    def setup_session(self):
        if self.session is None:
            self.session = ClientSession()
            _LOGGER.debug("New session created.")
            self._close_session = True

    @staticmethod
    def _build_url(uri: str, base_url: str | None = None) -> str:
        if base_url is None:
            base_url = OAUTH_AUTH_BASE_URL
        return str(URL(base_url).join(URL(uri)))

    async def _get_hashing_instructions(self, email: str) -> HashingInstructions:
        """Fetch hashing instructions from the server."""
        async with self.session.post(
            self._build_url("getHashingInstructions"),
            json={"email": email},
            headers=self.request_header,
            raise_for_status=True,
        ) as response:
            data = await response.json()
            return HashingInstructions.from_dict(data)

    async def _get_callback_url(self) -> URL:
        """Get callback url."""
        async with self.session.get(
            self._build_url("auth/web/login", OAUTH_LOGIN_BASE_URL),
            params={
                "returnUrl": OAUTH_RETURN_URL,
            },
            headers=self.request_header,
            raise_for_status=True,
        ) as response:
            return response.history[-1].url

    async def _login(self, auth_email: str, auth_password: str, hashing_instructions: HashingInstructions):
        """Login."""

        # Generate hashed password
        algo = parse_hashing_algorithm(hashing_instructions.current.algorithm)
        hashed_password = scrypt.hash(
            auth_password, hashing_instructions.current.salt, algo["n"], algo["r"], algo["p"], algo["dkLen"]
        ).hex()

        async with self.session.post(
            self._build_url("logginn"),
            json={
                "username": auth_email,
                "password": auth_password,
                "hashedPassword": {
                    "current": {
                        "recipe": hashing_instructions.current.to_dict(),
                        "hash": hashed_password,
                    },
                    "next": None,
                },
                "clientId": OAUTH_CLIENT_ID,
                "addUser": False,
            },
            params={
                "encodedExitUrl": quote_plus(OAUTH_RETURN_URL),
            },
            headers=self.request_header,
            raise_for_status=True,
        ) as response:
            user_data = await response.json()
            _LOGGER.debug("Got user data: %s", user_data)

    async def _finalize_login(self, params: dict[str, str]) -> dict:
        # Finalize auth flow
        async with self.session.get(
            self._build_url("connect/authorize/callback"),
            params=params,
            headers=self.request_header,
            raise_for_status=True,
        ) as response:
            await response.text()

        # Fetch token
        async with self.session.post(
            self._build_url("auth/session/tokenforsub/_", OAUTH_LOGIN_BASE_URL),
            headers=self.request_header,
            raise_for_status=True,
        ) as response:
            return await response.json()

    async def authorize(self, auth_email: str, auth_password: str):
        """Authorize."""
        try:
            callback_url = await self._get_callback_url()
            hashing_instructions = await self._get_hashing_instructions(auth_email)
            await self._login(auth_email, auth_password, hashing_instructions)

            callback_params = dict(callback_url.query)
            auth_data = await self._finalize_login(callback_params)
            return NrkAuthData.from_dict(auth_data)
        except TimeoutError as exception:
            raise NrkPsApiConnectionTimeoutError("Timed out while waiting for server response") from exception
        except (ClientError, ClientResponseError) as err:
            raise NrkPsApiAuthenticationError("Authentication error") from err

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self):
        """Async enter."""
        self.setup_session()
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit."""
        await self.close()
