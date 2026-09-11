class CxError(Exception):
    """Base class for all Checkmarx client errors."""


class CxConnectionError(CxError):
    """Network/DNS/timeout error reaching a Checkmarx One endpoint."""


class CxAuthError(CxError):
    """Authentication failed (bad credentials, expired/invalid refresh token, etc.)."""


class CxApiError(CxError):
    """Non-2xx response from a Checkmarx One API other than an auth failure."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code
