from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import DateTime, String, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from db.model import Base
from base.date import get_utc_now


__all__ = ["Docs", "DocStatus"]


class DocStatus(Enum):
    UPLOAD_REQUESTED = "UPLOAD_REQUESTED"
    UPLOADED = "UPLOADED"
    INDEXING = "INDEXING"
    INDEXED = "INDEXED"

    UPLOAD_FAILED = "UPLOAD_FAILED"
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
    READ_FAILED = "FILE_READ_FAILED"
    SPLITTING_FAILED = "SPLITTING_FAILED"
    INDEXING_FAILED = "INDEXING_FAILED"

    RETRYING = "RETRYING"


class Docs(Base):
    __tablename__ = "docs"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    size: Mapped[int] = mapped_column(nullable=False, comment="bytes")
    extension: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[DocStatus] = mapped_column(
        SAEnum(DocStatus, native_enum=False, length=32),
        default=DocStatus.UPLOAD_REQUESTED,
        nullable=False,
    )

    bucket: Mapped[str] = mapped_column(String(64), nullable=False)
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now
    )

    @staticmethod
    def of(
        id: UUID, name: str, size: int, extension: str, bucket: str, key: str
    ) -> Docs:
        return Docs(
            id=id, name=name, size=size, extension=extension, bucket=bucket, key=key
        )
