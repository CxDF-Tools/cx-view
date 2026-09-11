from dataclasses import dataclass
from datetime import datetime


@dataclass
class Project:
    id: str
    name: str
    created_at: datetime | None


@dataclass
class Scan:
    id: str
    project_id: str
    status: str | None
    created_at: datetime | None


@dataclass
class CxUser:
    id: str
    email: str | None
    username: str | None
    last_login: datetime | None
