import uuid

from sqlalchemy import update
from sqlalchemy.orm import Session
from docs.models.doc_model import DocStatus, Docs


class DocTaskRepository:
    def update_status(self, session: Session, doc_id: uuid.UUID, status: DocStatus):
        stmt = update(Docs).where(Docs.id == doc_id).values(status=status.value)
        session.execute(stmt)
