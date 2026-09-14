import base64
import json
import time

import httpx
import pytest

from app.cx_client.auth import TokenManager
from app.cx_client.exceptions import CxAuthError, CxConnectionError


def _make_jwt(claims: dict) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    return f"{header}.{payload}.sig"


def _mock_client(handler) -> httpx.Client:
    transport = httpx.MockTransport(handler)
    return httpx.Client(transport=transport)


def test_refresh_token_grant_success():
    access_token = _make_jwt({"ast-license": {"LicenseData": {"expirationDate": 1893456000000}}})

    def handler(request):
        assert request.url.path.endswith("/protocol/openid-connect/token")
        return httpx.Response(200, json={"access_token": access_token, "expires_in": 300})

    tm = TokenManager(
        iam_url="https://iam.example.com",
        tenant_id="acme",
        auth_method="refresh_token",
        refresh_token="rt-123",
        http_client=_mock_client(handler),
    )
    token = tm.get_access_token()
    assert token == access_token
    assert tm.latest_license_expiration is not None
    assert tm.latest_license_expiration.year == 2030


def test_client_credentials_grant_success():
    access_token = _make_jwt({})

    def handler(request):
        return httpx.Response(200, json={"access_token": access_token, "expires_in": 300})

    tm = TokenManager(
        iam_url="https://iam.example.com",
        tenant_id="acme",
        auth_method="client_credentials",
        client_id="cid",
        client_secret="csecret",
        http_client=_mock_client(handler),
    )
    assert tm.get_access_token() == access_token
    assert tm.latest_license_expiration is None


def test_invalid_credentials_raise_auth_error():
    def handler(request):
        return httpx.Response(401, text="invalid_grant")

    tm = TokenManager(
        iam_url="https://iam.example.com",
        tenant_id="acme",
        auth_method="refresh_token",
        refresh_token="not-a-real-token",  # test fixture value, not a live credential
        http_client=_mock_client(handler),
    )
    with pytest.raises(CxAuthError):
        tm.get_access_token()


def test_network_error_raises_connection_error():
    def handler(request):
        raise httpx.ConnectError("boom")

    tm = TokenManager(
        iam_url="https://iam.example.com",
        tenant_id="acme",
        auth_method="refresh_token",
        refresh_token="rt-123",
        http_client=_mock_client(handler),
    )
    with pytest.raises(CxConnectionError):
        tm.get_access_token()


def test_token_is_cached_until_near_expiry():
    access_token = _make_jwt({})
    call_count = {"n": 0}

    def handler(request):
        call_count["n"] += 1
        return httpx.Response(200, json={"access_token": access_token, "expires_in": 300})

    tm = TokenManager(
        iam_url="https://iam.example.com",
        tenant_id="acme",
        auth_method="refresh_token",
        refresh_token="rt-123",
        http_client=_mock_client(handler),
    )
    tm.get_access_token()
    tm.get_access_token()
    assert call_count["n"] == 1

    tm._expires_at = time.time() - 1
    tm.get_access_token()
    assert call_count["n"] == 2


def test_original_refresh_token_is_always_reused_not_the_rotated_one():
    """Checkmarx's API Key (the refresh_token users paste in) is meant to be a stable,
    long-lived credential reused on every call, like the official cx CLI does. Keycloak's
    response also includes a short-lived rotated `refresh_token` field; TokenManager must
    NOT adopt it as a replacement, or the connection breaks once that rotated token's own
    (much shorter) lifetime elapses."""
    access_token = _make_jwt({})
    sent_refresh_tokens = []

    def handler(request):
        body = request.read().decode()
        sent_refresh_tokens.append(dict(part.split("=") for part in body.split("&"))["refresh_token"])
        return httpx.Response(
            200,
            json={"access_token": access_token, "expires_in": 300, "refresh_token": "rotated-ephemeral-token"},
        )

    tm = TokenManager(
        iam_url="https://iam.example.com",
        tenant_id="acme",
        auth_method="refresh_token",
        refresh_token="original-stable-api-key",
        http_client=_mock_client(handler),
    )
    tm.get_access_token()
    tm._expires_at = time.time() - 1  # force a second token fetch
    tm.get_access_token()

    assert sent_refresh_tokens == ["original-stable-api-key", "original-stable-api-key"]


def test_missing_credentials_raise_value_error():
    with pytest.raises(ValueError):
        TokenManager(iam_url="https://iam.example.com", tenant_id="acme", auth_method="refresh_token")
    with pytest.raises(ValueError):
        TokenManager(iam_url="https://iam.example.com", tenant_id="acme", auth_method="client_credentials")
