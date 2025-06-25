from typing import Type, List

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from clients.elasticsearch.schema import DocSchema

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

    async def index_docs(self, docs: List[DocSchema], index_name: str):
        await async_bulk(
            client=self.es_client,
            actions=[
                {
                    "_source": doc.model_dump(),
                }
                for doc in docs
            ],
            index=index_name,
            refresh=True,
        )

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
