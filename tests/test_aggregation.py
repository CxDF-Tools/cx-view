from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.cx_client.models import CxUser, Project, Scan
from app.services.project_summary import build_project_summary
from app.services.user_summary import build_user_summary


def _dt(y, m, d):
    return datetime(y, m, d, tzinfo=timezone.utc)


def test_project_summary_basic():
    client = MagicMock()
    client.list_projects.return_value = [
        Project(id="1", name="Alpha", created_at=_dt(2023, 1, 1)),
        Project(id="2", name="Beta", created_at=_dt(2024, 6, 1)),
    ]
    client.list_scans.return_value = [Scan(id="s1", project_id="2", status="Completed", created_at=_dt(2024, 6, 5))]

    summary = build_project_summary(client)

    assert summary.total_count == 2
    assert summary.first_added_at == _dt(2023, 1, 1)
    assert summary.most_recently_added_name == "Beta"
    assert summary.last_scanned_project_name == "Beta"
    assert summary.last_scanned_at == _dt(2024, 6, 5)


def test_project_summary_empty_tenant():
    client = MagicMock()
    client.list_projects.return_value = []
    client.list_scans.return_value = []

    summary = build_project_summary(client)

    assert summary.total_count == 0
    assert summary.first_added_at is None
    assert summary.last_scanned_project_name is None


def test_user_summary_excludes_filtered_emails_and_limits_to_five():
    client = MagicMock()
    users = [CxUser(id=str(i), email=f"user{i}@example.com", username=f"user{i}", last_login=_dt(2024, 1, i)) for i in range(1, 8)]
    users.append(CxUser(id="ai", email="ai-assist@noreply.checkmarx.com", username="ai", last_login=_dt(2024, 1, 20)))
    users.append(CxUser(id="df", email="david.flynn@checkmarx.com", username="dave", last_login=_dt(2024, 1, 21)))
    client.list_users.return_value = users

    summary = build_user_summary(client)

    assert summary.total_count == 7
    assert len(summary.recent_logins) == 5
    emails = [row.email for row in summary.recent_logins]
    assert "ai-assist@noreply.checkmarx.com" not in emails
    assert "david.flynn@checkmarx.com" not in emails
    assert emails[0] == "user7@example.com"


def test_user_summary_sorts_most_recent_login_first_regardless_of_input_order():
    client = MagicMock()
    # Deliberately shuffled/out-of-order input to prove the sort isn't just input order.
    client.list_users.return_value = [
        CxUser(id="1", email="mid@example.com", username="mid", last_login=_dt(2024, 6, 1)),
        CxUser(id="2", email="oldest@example.com", username="oldest", last_login=_dt(2024, 1, 1)),
        CxUser(id="3", email="newest@example.com", username="newest", last_login=_dt(2024, 12, 1)),
        CxUser(id="4", email="no-login@example.com", username="no-login", last_login=None),
    ]

    summary = build_user_summary(client)

    emails_in_order = [row.email for row in summary.recent_logins]
    assert emails_in_order == [
        "newest@example.com",
        "mid@example.com",
        "oldest@example.com",
        "no-login@example.com",
    ]


def test_user_summary_fewer_than_five_users():
    client = MagicMock()
    client.list_users.return_value = [
        CxUser(id="1", email="a@example.com", username="a", last_login=_dt(2024, 1, 1)),
        CxUser(id="2", email="b@example.com", username="b", last_login=None),
    ]

    summary = build_user_summary(client)

    assert summary.total_count == 2
    assert len(summary.recent_logins) == 2
