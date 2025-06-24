from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    AWS_ENDPOINT_URL: str = Field(default="http://localhost:4566")
    AWS_ACCESS_KEY_ID: str = Field(default="test")
    AWS_SECRET_ACCESS_KEY: str = Field(default="test")
    AWS_REGION: str = Field(default="ap-northeast-2")

    ELASTICSEARCH_ENDPOINT: List[str] = Field(default=["http://localhost:9200"])
    ELASTICSEARCH_INDEX: str = Field(default="documents")

    S3_DOCS_BUCKET: str = Field(default="documents")
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

    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_BACKEND_URL: str = Field(default="redis://localhost:6379/1")
