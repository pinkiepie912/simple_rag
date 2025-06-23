from typing import Type

from clients.elasticsearch.schema import DocSchema

TOKENIZER_NAME = "kr_tokenizer"
FILTER_NAME = "kr_filter"
ANALYZER_NAME = "kr_analyzer"


class ElasticsearchInitializer:
    def __init__(self, es_client, index_name):
        self.es_client = es_client
        self.index_name = index_name

    def create_idx(self, schema: Type[DocSchema], clear=False):
        idx_exists = self.es_client.indices.exists(index=self.index_name)
        if idx_exists and not clear:
            return

        if idx_exists:
            self.es_client.indices.delete(index=self.index_name)

        self.es_client.indices.create(
            index=self.index_name,
            body={
                "settings": {"analysis": self._get_settings()},
                "mappings": {"properties": schema.create_map(ANALYZER_NAME)},
            },
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
