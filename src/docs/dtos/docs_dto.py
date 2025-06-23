from pydantic import BaseModel, Field
from base.dto import ReqResBaseModel

__all__ = [
    "GetUploadUrlRequest",
    "GetUploadUrlResponse",
    "GetUploadUrlMetadata",
]


class GetUploadUrlRequest(ReqResBaseModel):
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


class GetUploadUrlMetadata(ReqResBaseModel):
    doc_id: str


class GetUploadUrlResponse(ReqResBaseModel):
    presigned_url: str = Field(..., alias="presignedUrl")
    metadata: GetUploadUrlMetadata


class PresignedUrlDto(BaseModel):
    url: str
    doc_id: str
