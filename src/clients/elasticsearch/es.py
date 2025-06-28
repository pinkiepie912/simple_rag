from typing import Type, List

from elasticsearch import AsyncElasticsearch

from clients.elasticsearch.schema import DocSchema

__all__ = ["EsClient"]

TOKENIZER_NAME = "kr_tokenizer"
FILTER_NAME = "kr_filter"
ANALYZER_NAME = "kr_analyzer"


class EsClient:
    def __init__(self, es_client: AsyncElasticsearch):
        self.es_client = es_client

    async def create_idx(self, schema: Type[DocSchema], index_name: str, clear=False):
        idx_exists = await self.es_client.indices.exists(index=index_name)
        if idx_exists and not clear:
            return

        if idx_exists:
            await self.es_client.indices.delete(index=index_name)

        await self.es_client.indices.create(
            index=index_name,
            body={
                "settings": {"analysis": self._get_settings()},
                "mappings": {"properties": schema.create_map(ANALYZER_NAME)},
            },
        )

    async def search_docs(
        self, index_name: str, doc_id: str, query: str, size: int = 10
    ) -> List[DocSchema]:
        res = await self.es_client.search(
            index=index_name,
            body={
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "content": {
                                        "query": query,
                                        "analyzer": ANALYZER_NAME,
                                    }
                                }
                            },
                        ],
                        "filter": [
                            {
                                "term": {
                                    "doc_id": doc_id,
                                }
                            }
                        ],
                    },
                },
                "size": size,
            },
        )

        hits = res.get("hits", {}).get("hits", [])
        return [DocSchema(**hit["_source"]) for hit in hits]

    def _get_settings(self) -> dict:
        return {
            "tokenizer": {
                TOKENIZER_NAME: {
                    "type": "nori_tokenizer",
                    "decompound_mode": "mixed",
                }
            },
            "filter": {
                FILTER_NAME: {
                    "type": "nori_part_of_speech",
                    "stoptags": [
                        "JKS",
                        "JKC",
                        "JKG",
                        "JKO",
                        "JKB",
                        "JKV",
                        "JKQ",
                        "JX",
                        "JC",
                        "EP",
                        "EF",
                        "EC",
                        "ETN",
                        "ETM",
                        "XPN",
                        "XSN",
                        "XSV",
                        "XSA",
                        "SF",
                        "SP",
                        "SE",
                    ],
                }
            },
            "analyzer": {
                ANALYZER_NAME: {
                    "type": "custom",
                    "tokenizer": TOKENIZER_NAME,
                    "filter": ["lowercase", FILTER_NAME],
                }
            },
        }
