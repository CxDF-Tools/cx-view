from dataclasses import dataclass
from datetime import datetime

from app.config import EXCLUDED_USER_EMAILS
from app.cx_client.client import CheckmarxClient

TOP_N = 5


@dataclass
class UserSummaryRow:
    email: str | None
    username: str | None
    last_login: datetime | None


@dataclass
class UserSummary:
    total_count: int
    recent_logins: list[UserSummaryRow]


def build_user_summary(client: CheckmarxClient) -> UserSummary:
    users = client.list_users()
    eligible = [u for u in users if (u.email or "").lower() not in EXCLUDED_USER_EMAILS]

    with_login = sorted(
        (u for u in eligible if u.last_login is not None), key=lambda u: u.last_login, reverse=True
    )
    without_login = [u for u in eligible if u.last_login is None]
    top = (with_login + without_login)[:TOP_N]

    return UserSummary(
        total_count=len(eligible),
        recent_logins=[UserSummaryRow(email=u.email, username=u.username, last_login=u.last_login) for u in top],
    )
