from typing import TypeAlias

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from docs.models.doc_model import Docs

SessionType: TypeAlias = Session | AsyncSession


class DocRepository:

    def create_doc(self, session: SessionType, doc: Docs):
        session.add(doc)
