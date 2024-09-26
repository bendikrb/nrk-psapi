"""nrk-psapi exceptions."""


class NrkPsApiError(Exception):
    """Generic NrkPs exception."""


class NrkPsApiNotFoundError(NrkPsApiError):
    """NrkPs not found exception."""


class NrkPsApiConnectionError(NrkPsApiError):
    """NrkPs connection exception."""


class NrkPsApiConnectionTimeoutError(NrkPsApiConnectionError):
    """NrkPs connection timeout exception."""


class NrkPsApiRateLimitError(NrkPsApiConnectionError):
    """NrkPs Rate Limit exception."""


class NrkPsApiAuthenticationError(NrkPsApiError):
    """NrkPs authentication exception."""


class NrkPsAuthorizationError(NrkPsApiError):
    """NrkPs authorization error."""


class NrkPsAccessDeniedError(NrkPsApiError):
    """NrkPs access denied error."""
