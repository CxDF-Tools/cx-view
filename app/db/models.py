from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Connection(Base):
    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_name: Mapped[str] = mapped_column(String, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String, nullable=False)
    base_api_url: Mapped[str] = mapped_column(String, nullable=False)
    iam_url: Mapped[str] = mapped_column(String, nullable=False)
    auth_method: Mapped[str] = mapped_column(String, nullable=False)  # refresh_token | client_credentials

    refresh_token_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_id_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_secret_enc: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_test_status: Mapped[str | None] = mapped_column(String, nullable=True)
    last_test_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    license_expiration_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
