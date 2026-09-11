from dataclasses import dataclass
from datetime import datetime

from app.cx_client.client import CheckmarxClient


@dataclass
class ProjectSummary:
    total_count: int
    first_added_at: datetime | None
    most_recently_added_at: datetime | None
    most_recently_added_name: str | None
    last_scanned_project_name: str | None
    last_scanned_at: datetime | None


def build_project_summary(client: CheckmarxClient) -> ProjectSummary:
    projects = client.list_projects()
    dated_projects = [p for p in projects if p.created_at is not None]

    first_added = min(dated_projects, key=lambda p: p.created_at) if dated_projects else None
    most_recent = max(dated_projects, key=lambda p: p.created_at) if dated_projects else None

    last_scanned_name: str | None = None
    last_scanned_at: datetime | None = None
    scans = client.list_scans(limit=1, sort="-created_at")
    if scans:
        latest_scan = scans[0]
        last_scanned_at = latest_scan.created_at
        matching = next((p for p in projects if p.id == latest_scan.project_id), None)
        last_scanned_name = matching.name if matching else latest_scan.project_id

    return ProjectSummary(
        total_count=len(projects),
        first_added_at=first_added.created_at if first_added else None,
        most_recently_added_at=most_recent.created_at if most_recent else None,
        most_recently_added_name=most_recent.name if most_recent else None,
        last_scanned_project_name=last_scanned_name,
        last_scanned_at=last_scanned_at,
    )
