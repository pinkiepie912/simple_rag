import boto3
from elasticsearch import AsyncElasticsearch
from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from clients.elasticsearch.es import EsClient
from clients.s3.s3 import S3Client
from docs.services.doc_writer import DocWriter
from db.db import ReadSessionManager, WriteSessionManager


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    wiring_config = containers.WiringConfiguration(
        modules=["docs.router", "docs.tasks"]
    )

    # SqlAlchemy
    _write_db_engine = providers.Singleton(
        create_async_engine,
        url=providers.Callable(
            "mysql+aiomysql://{user}:{password}@{url}/{name}".format,
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
        async_sessionmaker, bind=_write_db_engine, class_=AsyncSession
    )

    _read_db_engine = providers.Singleton(
        create_async_engine,
        url=providers.Callable(
            "mysql+aiomysql://{user}:{password}@{url}/{name}".format,
            user=config.DATABASE.READ_USER,
            password=config.DATABASE.READ_PASSWORD,
            url=config.DATABASE.READ_URL,
            name=config.DATABASE.READ_NAME,
        ),
        pool_size=config.DATABASE.POOL_SIZE,
        max_overflow=config.DATABASE.MAX_OVERFLOW,
        pool_timeout=config.DATABASE.POOL_TIMEOUT,
        pool_recycle=config.DATABASE.POOL_RECYCLE,
        pool_pre_ping=config.DATABASE.POOL_PRE_PING,
    )
    _read_db_session_maker = providers.Singleton(
        async_sessionmaker, bind=_read_db_engine, class_=AsyncSession
    )

    read_session_manager = providers.Factory(
        ReadSessionManager,
        session_maker=_read_db_session_maker,
    )

    write_session_manager = providers.Factory(
        WriteSessionManager,
        session_maker=_write_db_session_maker,
    )

    # Elasticsearch
    _es = providers.Singleton(AsyncElasticsearch, hosts=config.ELASTICSEARCH.ENDPOINT)
    es_client = providers.Factory(
        EsClient,
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

    # docs
    doc_writer = providers.Factory(
        DocWriter,
        s3_client=s3_client,
        es_client=es_client,
        bucket_name=config.S3.DOCS_BUCKET,
        allowed_extensions=config.DOCUMENT.ALLOWED_EXTENSIONS,
        doc_size_limit=config.DOCUMENT.DOC_SIZE_LIMIT,
        write_session_manager=write_session_manager,
        doc_index_name=config.ELASTICSEARCH.INDEX,
    )
