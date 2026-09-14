from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import Connection
from app.security.crypto import decrypt_str, encrypt_str


def create_connection(
    db: Session,
    *,
    tenant_name: str,
    tenant_id: str,
    base_api_url: str,
    iam_url: str,
    auth_method: str,
    refresh_token: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
) -> Connection:
    conn = Connection(
        tenant_name=tenant_name,
        tenant_id=tenant_id,
        base_api_url=base_api_url.rstrip("/"),
        iam_url=iam_url.rstrip("/"),
        auth_method=auth_method,
        refresh_token_enc=encrypt_str(refresh_token),
        client_id_enc=encrypt_str(client_id),
        client_secret_enc=encrypt_str(client_secret),
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


def list_connections(db: Session) -> list[Connection]:
    return list(db.query(Connection).order_by(Connection.tenant_name).all())


def get_connection(db: Session, connection_id: int) -> Connection | None:
    return db.get(Connection, connection_id)


def delete_connection(db: Session, connection_id: int) -> None:
    conn = db.get(Connection, connection_id)
    if conn is not None:
        db.delete(conn)
        db.commit()


def decrypted_credentials(conn: Connection) -> dict[str, str | None]:
    return {
        "refresh_token": decrypt_str(conn.refresh_token_enc),
        "client_id": decrypt_str(conn.client_id_enc),
        "client_secret": decrypt_str(conn.client_secret_enc),
    }


def record_test_result(
    db: Session,
    connection_id: int,
    *,
    ok: bool,
    message: str,
    license_expiration_at: datetime | None,
) -> None:
    conn = db.get(Connection, connection_id)
    if conn is None:
        return
    conn.last_test_status = "ok" if ok else "error"
    conn.last_test_message = message
    if ok:
        conn.last_verified_at = datetime.now(conn.created_at.tzinfo) if conn.created_at.tzinfo else datetime.utcnow()
        if license_expiration_at is not None:
            conn.license_expiration_at = license_expiration_at
    db.commit()
