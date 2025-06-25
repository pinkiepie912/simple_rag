import boto3
from elasticsearch import AsyncElasticsearch
from dependency_injector import containers, providers

from config.config import Config
from clients.elasticsearch.es import EsClient
from docs.services.doc_writer import DocWriter


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=["docs.router", "docs.tasks"]
    )

    config = providers.Singleton(Config)

    # Elasticsearch
    es = providers.Singleton(
        AsyncElasticsearch, hosts=config.provided.ELASTICSEARCH_ENDPOINT
    )
    es_client = providers.Factory(
        EsClient,
        es_client=es,
    )

    # s3
    s3_client = providers.Singleton(
        boto3.client,
        service_name="s3",
        region_name=config.provided.AWS_REGION,
        aws_access_key_id=config.provided.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.provided.AWS_SECRET_ACCESS_KEY,
        endpoint_url=config.provided.AWS_ENDPOINT_URL,
    )

    # docs
    doc_writer = providers.Factory(
        DocWriter,
        s3_client=s3_client,
        es_client=es_client,
        bucket_name=config.provided.S3_DOCS_BUCKET,
        allowed_extensions=config.provided.ALLOWED_EXTENSIONS,
        doc_size_limit=config.provided.DOC_SIZE_LIMIT,
    )
