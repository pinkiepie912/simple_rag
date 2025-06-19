from clients.elasticsearch.dto import DocumentDTO


class ElasticsearchWriter:
    def __init__(self, es_client, index_name):
        self.es_client = es_client
        self.index_name = index_name

    def index_doc(self, document: DocumentDTO):
        self.es_client.index(
            index=self.index_name,
            id=document.doc_id,
            body={"content": document.content, "metadata": document.metadata},
        )
