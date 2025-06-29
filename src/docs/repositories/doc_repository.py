from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from docs.models.doc_model import Docs


class DocRepository:

    def create_doc(self, session: AsyncSession, doc: Docs):
        session.add(doc)

    async def get_doc(self, session: AsyncSession, doc_id: UUID) -> Docs | None:
        return await session.get(Docs, doc_id)
