from __future__ import annotations

import uuid

from pydantic import BaseModel, Field
from base.dto import SnakeToCamelBaseModel
from docs.models.doc_model import DocStatus

__all__ = [
    "GetUploadUrlRequest",
    "GetUploadUrlResponse",
    "GetUploadUrlMetadata",
    "PresignedUrlDto",
    "IndexDocsParams",
    "SearchDocsRequest",
    "GetDocRequest",
    "DocResponse",
]


class GetUploadUrlRequest(SnakeToCamelBaseModel):
    filename: str = Field(
        ...,
        description="Name of the file with extension.",
        examples=["example.pdf"],
    )
    size: int = Field(
        ...,
        gt=0,
        description="File size in bytes. Must be greater than 0.",
        examples=[1024],
    )


class GetUploadUrlMetadata(SnakeToCamelBaseModel):
    doc_id: str


class GetUploadUrlResponse(SnakeToCamelBaseModel):
    presigned_url: str = Field(..., alias="presignedUrl")
    metadata: GetUploadUrlMetadata


class PresignedUrlDto(BaseModel):
    url: str
    doc_id: str


class IndexDocsParams(SnakeToCamelBaseModel):
    key: str
    chunk_size: int = Field(default=1024)
    chunk_overlap_ratio: float = Field(default=0.2)


class SearchDocsRequest(SnakeToCamelBaseModel):
    doc_id: str
    question: str


class SearchDoc(SnakeToCamelBaseModel):
    doc_id: uuid.UUID
    content: str

    @staticmethod
    def of(doc_id: uuid.UUID, content: str) -> SearchDoc:
        return SearchDoc(doc_id=doc_id, content=content)


class SearchDocsResponse(SnakeToCamelBaseModel):
    docs: list[SearchDoc]

    @staticmethod
    def of(docs: list[SearchDoc]) -> SearchDocsResponse:
        return SearchDocsResponse(docs=docs)


class DocResponse(SnakeToCamelBaseModel):
    doc_id: uuid.UUID
    name: str
    size: int
    extension: str
    status: DocStatus
