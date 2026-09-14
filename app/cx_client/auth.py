import base64
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from app.cx_client.exceptions import CxAuthError, CxConnectionError

logger = logging.getLogger(__name__)

TOKEN_EXPIRY_SAFETY_MARGIN_SECONDS = 30


@dataclass
class TokenResult:
    access_token: str
    expires_at: float
    license_expiration: datetime | None


def _decode_jwt_claims(token: str) -> dict:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:
        logger.exception("Failed to decode JWT claims from access token")
        return {}


def _extract_license_expiration(claims: dict) -> datetime | None:
    try:
        expiry_ms = claims["ast-license"]["LicenseData"]["expirationDate"]
        return datetime.fromtimestamp(expiry_ms / 1000, tz=timezone.utc)
    except (KeyError, TypeError, ValueError):
        logger.debug("No ast-license expiration claim found on access token")
        return None


class TokenManager:
    """Acquires and caches Checkmarx One access tokens for a single tenant connection.

    Supports both the refresh-token grant and the client-credentials grant against
    the Keycloak-based IAM token endpoint.

    Checkmarx One's "API Key" is a long-lived, stable credential meant to be reused
    indefinitely (the official cx CLI always sends back the same original value it
    was configured with). Keycloak's token response also includes a short-lived
    rotated `refresh_token` field, but that one is NOT the API Key and expires in
    hours if unused — treating it as a replacement for the original API Key (as an
    earlier version of this class did) silently breaks the connection once that
    rotated token's own short window elapses. So we always re-send the original
    refresh_token we were constructed with, and ignore whatever comes back.
    """

    def __init__(
        self,
        *,
        iam_url: str,
        tenant_id: str,
        auth_method: str,
        refresh_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        http_client: httpx.Client | None = None,
    ):
        if auth_method not in ("refresh_token", "client_credentials"):
            raise ValueError(f"Unsupported auth_method: {auth_method}")
        if auth_method == "refresh_token" and not refresh_token:
            raise ValueError("refresh_token is required for auth_method=refresh_token")
        if auth_method == "client_credentials" and not (client_id and client_secret):
            raise ValueError("client_id and client_secret are required for auth_method=client_credentials")

        self._iam_url = iam_url.rstrip("/")
        self._tenant_id = tenant_id
        self._auth_method = auth_method
        self._refresh_token = refresh_token
        self._client_id = client_id
        self._client_secret = client_secret
        self._http = http_client or httpx.Client(timeout=15.0)
        self._owns_http_client = http_client is None

        self._access_token: str | None = None
        self._expires_at: float = 0.0
        self.latest_license_expiration: datetime | None = None

    def close(self) -> None:
        if self._owns_http_client:
            self._http.close()

    def _token_endpoint(self) -> str:
        return f"{self._iam_url}/auth/realms/{self._tenant_id}/protocol/openid-connect/token"

    def get_access_token(self) -> str:
        if self._access_token is not None and time.time() < self._expires_at - TOKEN_EXPIRY_SAFETY_MARGIN_SECONDS:
            return self._access_token

        result = self._fetch_token()
        self._access_token = result.access_token
        self._expires_at = result.expires_at
        if result.license_expiration is not None:
            self.latest_license_expiration = result.license_expiration
        return self._access_token

    def _fetch_token(self) -> TokenResult:
        if self._auth_method == "refresh_token":
            data = {
                "grant_type": "refresh_token",
                "client_id": "ast-app",
                "refresh_token": self._refresh_token,
            }
        else:
            data = {
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            }

        try:
            response = self._http.post(self._token_endpoint(), data=data)
        except httpx.RequestError as exc:
            logger.warning("Could not reach IAM token endpoint: %s", exc)
            raise CxConnectionError(f"Could not reach IAM token endpoint: {exc}") from exc

        if response.status_code in (400, 401):
            logger.warning("IAM token endpoint rejected credentials (status %s)", response.status_code)
            raise CxAuthError(f"Authentication failed ({response.status_code}): {response.text[:300]}")
        if response.status_code >= 400:
            logger.warning("IAM token endpoint returned unexpected status %s", response.status_code)
            raise CxConnectionError(f"Unexpected error from IAM token endpoint ({response.status_code})")

        body = response.json()
        access_token = body.get("access_token")
        if not access_token:
            raise CxAuthError("Token response did not include an access_token")

        expires_in = body.get("expires_in", 300)
        claims = _decode_jwt_claims(access_token)
        license_expiration = _extract_license_expiration(claims)

        return TokenResult(
            access_token=access_token,
            expires_at=time.time() + expires_in,
            license_expiration=license_expiration,
        )
