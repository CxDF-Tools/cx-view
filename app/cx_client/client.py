import logging
from datetime import datetime, timezone

import httpx

from app.cx_client.auth import TokenManager
from app.cx_client.exceptions import CxApiError, CxAuthError, CxConnectionError
from app.cx_client.models import CxUser, Project, Scan

logger = logging.getLogger(__name__)

PAGE_SIZE = 100
MAX_PAGES = 50  # safety cap to avoid unbounded pagination on very large tenants


def _extract_items(body, key: str) -> list:
    """Checkmarx One list endpoints wrap results in an object like {"<key>": [...]}, but
    for an empty tenant the field can be present with an explicit null rather than []
    or an omitted key — dict.get(key, default) does not fall back to default in that case."""
    if isinstance(body, list):
        return body
    value = body.get(key) if isinstance(body, dict) else None
    return value if isinstance(value, list) else []


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        text = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        logger.debug("Could not parse datetime value: %s", value)
        return None


class CheckmarxClient:
    """Thin REST client for a single Checkmarx One tenant connection."""

    def __init__(self, *, base_api_url: str, iam_url: str, tenant_id: str, token_manager: TokenManager):
        self._base_api_url = base_api_url.rstrip("/")
        self._iam_url = iam_url.rstrip("/")
        self._tenant_id = tenant_id
        self._token_manager = token_manager
        self._http = httpx.Client(timeout=30.0)

    def close(self) -> None:
        self._http.close()
        self._token_manager.close()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token_manager.get_access_token()}"}

    def _get(self, url: str, params: dict | None = None) -> httpx.Response:
        try:
            response = self._http.get(url, params=params, headers=self._headers())
        except httpx.RequestError as exc:
            raise CxConnectionError(f"Could not reach {url}: {exc}") from exc

        if response.status_code == 401:
            raise CxAuthError(f"Authentication rejected by {url}")
        if response.status_code >= 400:
            raise CxApiError(
                f"Request to {url} failed ({response.status_code}): {response.text[:300]}",
                status_code=response.status_code,
            )
        return response

    def test_connection(self) -> tuple[bool, str, datetime | None]:
        try:
            self._token_manager.get_access_token()
        except CxAuthError as exc:
            return False, str(exc), None
        except CxConnectionError as exc:
            return False, str(exc), None
        return True, "Connected successfully", self._token_manager.latest_license_expiration

    def list_projects(self) -> list[Project]:
        projects: list[Project] = []
        offset = 0
        for _ in range(MAX_PAGES):
            response = self._get(
                f"{self._base_api_url}/api/projects",
                params={"offset": offset, "limit": PAGE_SIZE},
            )
            items = _extract_items(response.json(), "projects")
            if not items:
                break
            for item in items:
                projects.append(
                    Project(
                        id=str(item.get("id")),
                        name=item.get("name", "(unnamed)"),
                        created_at=_parse_datetime(item.get("createdAt")),
                    )
                )
            if len(items) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
        return projects

    def list_scans(self, *, project_id: str | None = None, limit: int = 1, sort: str = "-created_at") -> list[Scan]:
        params: dict[str, str | int] = {"limit": limit, "sort": sort}
        if project_id:
            params["project-id"] = project_id
        response = self._get(f"{self._base_api_url}/api/scans", params=params)
        items = _extract_items(response.json(), "scans")
        return [
            Scan(
                id=str(item.get("id")),
                project_id=str(item.get("projectId") or item.get("project_id")),
                status=item.get("status"),
                created_at=_parse_datetime(item.get("createdAt")),
            )
            for item in items
        ]

    def list_users(self) -> list[CxUser]:
        users: list[CxUser] = []
        first = 0
        for _ in range(MAX_PAGES):
            response = self._get(
                f"{self._iam_url}/auth/admin/realms/{self._tenant_id}/users",
                params={"first": first, "max": PAGE_SIZE},
            )
            items = response.json()
            if not items:
                break
            for item in items:
                users.append(
                    CxUser(
                        id=str(item.get("id")),
                        email=item.get("email"),
                        username=item.get("username"),
                        last_login=self._extract_last_login(item),
                    )
                )
            if len(items) < PAGE_SIZE:
                break
            first += PAGE_SIZE
        return users

    @staticmethod
    def _extract_last_login(user: dict) -> datetime | None:
        for key in ("lastLogin", "lastLoginDate"):
            value = user.get(key)
            if value:
                if isinstance(value, (int, float)):
                    return datetime.fromtimestamp(value / 1000 if value > 1e12 else value, tz=timezone.utc)
                parsed = _parse_datetime(str(value))
                if parsed is not None:
                    return parsed
        attributes = user.get("attributes") or {}
        for key in ("lastLogin", "last_login"):
            values = attributes.get(key)
            if values:
                candidate = values[0] if isinstance(values, list) else values
                parsed = _parse_datetime(str(candidate))
                if parsed is not None:
                    return parsed
        return None
