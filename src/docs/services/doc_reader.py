from uuid import UUID
from clients.elasticsearch.es import EsClient
from clients.elasticsearch.schema import DocSchema
from db.db import ReadSessionManager
from docs.models.doc_model import Docs
from docs.repositories.doc_repository import DocRepository

__all__ = ["DocReader"]


class DocReader:
    def __init__(
        self,
        es_client: EsClient,
        doc_index_name: str,
        session_manager: ReadSessionManager,
        repo: DocRepository,
    ):
        self.es_client = es_client
        self.doc_index_name = doc_index_name
        self.session_manager = session_manager
        self.repo = repo

    async def get_doc(self, doc_id: UUID) -> Docs | None:
        async with self.session_manager as session:
            doc = await self.repo.get_doc(
                session=session,
                doc_id=doc_id,
            )
            return doc

    async def search_docs(
        self, question: str, doc_id: str, size: int = 10
    ) -> list[DocSchema]:
        docs = await self.es_client.search_docs(
            index_name=self.doc_index_name,
            doc_id=doc_id,
            query=question,
            size=size,
        )

        return docs
