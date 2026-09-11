import httpx

from app.cx_client.auth import TokenManager
from app.cx_client.client import CheckmarxClient


def _make_jwt() -> str:
    import base64
    import json

    header = base64.urlsafe_b64encode(b'{"alg":"none"}').decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({}).encode()).decode().rstrip("=")
    return f"{header}.{payload}.sig"


def _make_client(handler) -> CheckmarxClient:
    access_token = _make_jwt()

    def token_handler(request):
        return httpx.Response(200, json={"access_token": access_token, "expires_in": 300})

    token_manager = TokenManager(
        iam_url="https://iam.example.com",
        tenant_id="acme",
        auth_method="refresh_token",
        refresh_token="rt-123",
        http_client=httpx.Client(transport=httpx.MockTransport(token_handler)),
    )
    client = CheckmarxClient(
        base_api_url="https://ast.example.com",
        iam_url="https://iam.example.com",
        tenant_id="acme",
        token_manager=token_manager,
    )
    client._http = httpx.Client(transport=httpx.MockTransport(handler))
    return client


def test_list_projects_handles_explicit_null_list():
    def handler(request):
        return httpx.Response(200, json={"totalCount": 0, "filteredTotalCount": 0, "projects": None})

    client = _make_client(handler)
    assert client.list_projects() == []


def test_list_scans_handles_explicit_null_list():
    def handler(request):
        return httpx.Response(200, json={"totalCount": 0, "filteredTotalCount": 0, "scans": None})

    client = _make_client(handler)
    assert client.list_scans() == []


def test_list_projects_parses_normal_response():
    def handler(request):
        return httpx.Response(
            200,
            json={"projects": [{"id": "1", "name": "Alpha", "createdAt": "2024-01-01T00:00:00Z"}]},
        )

    client = _make_client(handler)
    projects = client.list_projects()
    assert len(projects) == 1
    assert projects[0].name == "Alpha"
