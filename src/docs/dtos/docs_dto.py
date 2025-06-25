from pydantic import BaseModel, Field
from base.dto import SnakeToCamelBaseModel

__all__ = [
    "GetUploadUrlRequest",
    "GetUploadUrlResponse",
    "GetUploadUrlMetadata",
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


class IndexDocsParams(BaseModel):
    index_name: str
    key: str
    chunk_size: int = Field(default=1024)
    chunk_overlap_ratio: float = Field(default=0.2)
