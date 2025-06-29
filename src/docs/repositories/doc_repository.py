from sqlalchemy.ext.asyncio import AsyncSession
from docs.models.doc_model import Docs


class DocRepository:

    def create_doc(self, session: AsyncSession, doc: Docs):
        session.add(doc)
