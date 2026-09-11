from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.cx_client.client import CheckmarxClient
from app.cx_client.exceptions import CxApiError, CxAuthError, CxConnectionError
from app.db.models import Connection
from app.services.project_summary import build_project_summary
from app.services.user_summary import build_user_summary
from app.templating import templates
from app.web.deps import get_active_connection, get_cx_client

router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
def chooser(request: Request, conn: Connection = Depends(get_active_connection)):
    return templates.TemplateResponse(request, "dashboard/chooser.html", {"connection": conn})


@router.get("/dashboard/projects", response_class=HTMLResponse)
def project_summary(
    request: Request,
    conn: Connection = Depends(get_active_connection),
    client: CheckmarxClient = Depends(get_cx_client),
):
    error = None
    summary = None
    try:
        summary = build_project_summary(client)
    except (CxAuthError, CxConnectionError, CxApiError) as exc:
        error = str(exc)
    finally:
        client.close()
    return templates.TemplateResponse(
        request, "dashboard/project_summary.html", {"connection": conn, "summary": summary, "error": error}
    )


@router.get("/dashboard/users", response_class=HTMLResponse)
def user_summary(
    request: Request,
    conn: Connection = Depends(get_active_connection),
    client: CheckmarxClient = Depends(get_cx_client),
):
    error = None
    summary = None
    try:
        summary = build_user_summary(client)
    except (CxAuthError, CxConnectionError, CxApiError) as exc:
        error = str(exc)
    finally:
        client.close()
    return templates.TemplateResponse(
        request, "dashboard/user_summary.html", {"connection": conn, "summary": summary, "error": error}
    )
