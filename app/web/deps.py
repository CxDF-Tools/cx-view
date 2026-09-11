from typing import Generator

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.cx_client.client import CheckmarxClient
from app.cx_client.auth import TokenManager
from app.db import crud
from app.db.database import get_session
from app.db.models import Connection
from app.web.session import get_active_connection_id


def get_db() -> Generator[Session, None, None]:
    yield from get_session()


def get_active_connection(request: Request, db: Session = Depends(get_db)) -> Connection:
    connection_id = get_active_connection_id(request)
    if connection_id is None:
        raise HTTPException(status_code=303, headers={"Location": "/"})
    conn = crud.get_connection(db, connection_id)
    if conn is None:
        raise HTTPException(status_code=303, headers={"Location": "/"})
    return conn


def build_cx_client(db: Session, conn: Connection) -> CheckmarxClient:
    creds = crud.decrypted_credentials(conn)

    def _persist_new_refresh_token(new_token: str) -> None:
        crud.update_refresh_token(db, conn.id, new_token)

    token_manager = TokenManager(
        iam_url=conn.iam_url,
        tenant_id=conn.tenant_id,
        auth_method=conn.auth_method,
        refresh_token=creds["refresh_token"],
        client_id=creds["client_id"],
        client_secret=creds["client_secret"],
        on_new_refresh_token=_persist_new_refresh_token if conn.auth_method == "refresh_token" else None,
    )
    return CheckmarxClient(
        base_api_url=conn.base_api_url,
        iam_url=conn.iam_url,
        tenant_id=conn.tenant_id,
        token_manager=token_manager,
    )


def get_cx_client(
    db: Session = Depends(get_db), conn: Connection = Depends(get_active_connection)
) -> CheckmarxClient:
    return build_cx_client(db, conn)
