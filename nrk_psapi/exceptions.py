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


class NrkPsAuthorizationSignInError(NrkPsApiError):
    """NrkPs authorization sign-in exception."""

    def __init__(self, err_no, err_msg):
        self.err_no = err_no
        self.err_msg = err_msg


class NrkPsAuthorizationError(NrkPsApiError):
    """NrkPs authorization error."""


class NrkPsAccessDeniedError(NrkPsApiError):
    """NrkPs access denied error."""
