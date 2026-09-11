from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.cx_client.exceptions import CxApiError, CxAuthError, CxConnectionError
from app.db import crud
from app.templating import templates
from app.web.deps import build_cx_client, get_db
from app.web.session import set_active_connection

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def list_connections(request: Request, db: Session = Depends(get_db)):
    connections = crud.list_connections(db)
    return templates.TemplateResponse(
        request, "connections/list.html", {"connections": connections}
    )


@router.get("/connections/new", response_class=HTMLResponse)
def new_connection_form(request: Request):
    return templates.TemplateResponse(request, "connections/new.html", {})


@router.post("/connections/new")
def create_connection(
    request: Request,
    db: Session = Depends(get_db),
    tenant_name: str = Form(...),
    tenant_id: str = Form(...),
    base_api_url: str = Form(...),
    iam_url: str = Form(...),
    auth_method: str = Form(...),
    refresh_token: str = Form(""),
    client_id: str = Form(""),
    client_secret: str = Form(""),
):
    crud.create_connection(
        db,
        tenant_name=tenant_name,
        tenant_id=tenant_id,
        base_api_url=base_api_url,
        iam_url=iam_url,
        auth_method=auth_method,
        refresh_token=refresh_token or None,
        client_id=client_id or None,
        client_secret=client_secret or None,
    )
    return RedirectResponse(url="/", status_code=303)


def _test_connection_result(db: Session, connection_id: int) -> dict:
    conn = crud.get_connection(db, connection_id)
    if conn is None:
        return {"ok": False, "message": "Connection not found"}
    client = build_cx_client(db, conn)
    try:
        ok, message, license_expiration_at = client.test_connection()
    except (CxAuthError, CxConnectionError, CxApiError) as exc:
        ok, message, license_expiration_at = False, str(exc), None
    finally:
        client.close()
    crud.record_test_result(db, connection_id, ok=ok, message=message, license_expiration_at=license_expiration_at)
    return {"ok": ok, "message": message, "license_expiration_at": license_expiration_at}


@router.post("/connections/{connection_id}/test", response_class=HTMLResponse)
def test_connection(request: Request, connection_id: int, db: Session = Depends(get_db)):
    result = _test_connection_result(db, connection_id)
    return templates.TemplateResponse(request, "connections/_test_result.html", result)


@router.post("/connections/{connection_id}/connect")
def connect(request: Request, connection_id: int, db: Session = Depends(get_db)):
    result = _test_connection_result(db, connection_id)
    if not result["ok"]:
        return RedirectResponse(url="/", status_code=303)
    set_active_connection(request, connection_id)
    return RedirectResponse(url="/dashboard", status_code=303)


@router.post("/connections/{connection_id}/delete")
def delete_connection(connection_id: int, db: Session = Depends(get_db)):
    crud.delete_connection(db, connection_id)
    return RedirectResponse(url="/", status_code=303)
