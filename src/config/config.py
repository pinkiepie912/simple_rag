from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["Config"]


class S3Config(BaseSettings):
    ENDPOINT_URL: str = Field(default="http://localhost:4566")
    ACCESS_KEY_ID: str = Field(default="test")
    SECRET_ACCESS_KEY: str = Field(default="test")
    REGION: str = Field(default="ap-northeast-2")

    DOCS_BUCKET: str = Field(default="documents")

    class Config:
        env_prefix = "AWS_"


class ElasticsearchConfig(BaseSettings):
    ENDPOINT: List[str] = Field(default=["http://localhost:9200"])
    INDEX: str = Field(default="documents")

    class Config:
        env_prefix = "ELASTICSEARCH_"


class DocumentConfig(BaseSettings):
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=[
            "pptx",
            "ppt",
            "docx",
            "doc",
            "hwp",
            "hwpx",
            "pdf",
            "txt",
            "json",
            "py",
        ]
    )
    DOC_SIZE_LIMIT: int = Field(default=20 * 1024 * 1024)


class CeleryConfig(BaseSettings):
    BROKER_URL: str = Field(default="redis://localhost:6379/0")
    BACKEND_URL: str = Field(default="redis://localhost:6379/1")

    class Config:
        env_prefix = "CELERY_"


class DatabaseConfig(BaseSettings):
    WRITE_URL: str = Field(default="localhost:3306")
    WRITE_USER: str = Field(default="rag")
    WRITE_PASSWORD: str = Field(default="rag")
    WRITE_NAME: str = Field(default="rag")

    READ_URL: str = Field(default="localhost:3306")
    READ_USER: str = Field(default="rag")
    READ_PASSWORD: str = Field(default="rag")
    READ_NAME: str = Field(default="rag")

    POOL_SIZE: int = Field(default=10)
    MAX_OVERFLOW: int = Field(default=5)
    POOL_TIMEOUT: int = Field(default=30)
    POOL_RECYCLE: int = Field(default=1800)
    POOL_PRE_PING: bool = Field(default=True)

    class Config:
        env_prefix = "DB_"


class Config(BaseSettings):
    APP_ENV: str = Field(default="dev")

    S3: S3Config = S3Config()
    ELASTICSEARCH: ElasticsearchConfig = ElasticsearchConfig()
    DOCUMENT: DocumentConfig = DocumentConfig()
    CELERY: CeleryConfig = CeleryConfig()
    DATABASE: DatabaseConfig = DatabaseConfig()

    model_config = SettingsConfigDict(case_sensitive=True)
