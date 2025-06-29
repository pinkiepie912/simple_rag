from typing import List
import uuid

from datetime import datetime
from collections.abc import Sequence

from sqlalchemy import and_, func, select, update
from sqlalchemy.orm import Session
from docs.models.doc_model import DocStatus, Docs


class DocTaskRepository:
    def update_status(
        self, session: Session, doc_ids: List[uuid.UUID], status: DocStatus
    ) -> None:
        stmt = update(Docs).where(Docs.id.in_(doc_ids)).values(status=status.value)
        session.execute(stmt)

    def fetch_docs_by_status(
        self,
        statuses: List[DocStatus],
        session: Session,
        cutoff_time: datetime,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Docs]:
        status_values = [row.value for row in statuses]
        stmt = (
            select(Docs)
            .where(and_(Docs.created_at <= cutoff_time, Docs.status.in_(status_values)))
            .order_by(Docs.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        return session.execute(stmt).scalars().all()

    def fetch_count_by_status(
        self,
        statuses: List[DocStatus],
        session: Session,
        cutoff_time: datetime,
    ) -> int:
        status_values = [row.value for row in statuses]
        stmt = (
            select(func.count(1))
            .select_from(Docs)
            .where(and_(Docs.created_at <= cutoff_time, Docs.status.in_(status_values)))
        )

        return session.execute(stmt).scalar() or 0
