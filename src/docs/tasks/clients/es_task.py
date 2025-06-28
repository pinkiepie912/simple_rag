from typing import List
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from clients.elasticsearch.schema import DocSchema

__all__ = ["EsTaskClient"]


class EsTaskClient:
    def __init__(self, es_client: Elasticsearch):
        self.es_client = es_client

    def index_docs(self, docs: List[DocSchema], index_name: str):
        bulk(
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
