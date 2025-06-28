from clients.elasticsearch.es import EsClient
from clients.elasticsearch.schema import DocSchema

__all__ = ["DocReader"]


class DocReader:
    def __init__(self, es_client: EsClient, doc_index_name: str):
        self.es_client = es_client
        self.doc_index_name = doc_index_name

    async def search_docs(self, question: str, doc_id: str, size: int = 10) -> list[DocSchema]:
        docs = await self.es_client.search_docs(
            index_name=self.doc_index_name,
            doc_id=doc_id,
            query=question,
            size=size,
        )

        return docs
