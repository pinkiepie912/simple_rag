import boto3
from dependency_injector import containers, providers
from elasticsearch import Elasticsearch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from clients.s3.s3 import S3Client
from db.db import WriteSessionSyncManager
from docs.tasks.clients.es_task import EsTaskClient
from docs.tasks.repositories.doc_task_repository import DocTaskRepository
from docs.tasks.services.doc_writer import DocWriter

__all__ = ["CeleryContainer"]


class CeleryContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    # SqlAlchemy
    _write_db_engine = providers.Singleton(
        create_engine,
        url=providers.Callable(
            "mysql+pymysql://{user}:{password}@{url}/{name}".format,
            user=config.DATABASE.WRITE_USER,
            password=config.DATABASE.WRITE_PASSWORD,
            url=config.DATABASE.WRITE_URL,
            name=config.DATABASE.WRITE_NAME,
        ),
        pool_size=config.DATABASE.POOL_SIZE,
        max_overflow=config.DATABASE.MAX_OVERFLOW,
        pool_timeout=config.DATABASE.POOL_TIMEOUT,
        pool_recycle=config.DATABASE.POOL_RECYCLE,
        pool_pre_ping=config.DATABASE.POOL_PRE_PING,
    )
    _write_db_session_maker = providers.Singleton(
        sessionmaker, bind=_write_db_engine, class_=Session
    )
    write_session_manager = providers.Factory(
        WriteSessionSyncManager,
        session_maker=_write_db_session_maker,
    )

    # Elasticsearch
    _es = providers.Singleton(Elasticsearch, hosts=config.ELASTICSEARCH.ENDPOINT)
    es_client = providers.Factory(
        EsTaskClient,
        es_client=_es,
    )

    # s3
    _s3_boto_client = providers.Singleton(
        boto3.client,
        service_name="s3",
        region_name=config.AWS.REGION,
        aws_access_key_id=config.AWS.ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS.SECRET_ACCESS_KEY,
        endpoint_url=config.AWS.ENDPOINT_URL,
    )

    s3_client = providers.Factory(
        S3Client,
        s3_client=_s3_boto_client,
    )

    doc_repository = providers.Factory(DocTaskRepository)

    doc_writer = providers.Factory(
        DocWriter,
        s3_client=s3_client,
        es_client=es_client,
        write_session_manager=write_session_manager,
        repo=doc_repository,
        bucket_name=config.S3.DOCS_BUCKET,
        allowed_extensions=config.DOCUMENT.ALLOWED_EXTENSIONS,
        doc_size_limit=config.DOCUMENT.DOC_SIZE_LIMIT,
        doc_index_name=config.ELASTICSEARCH.INDEX,
    )
