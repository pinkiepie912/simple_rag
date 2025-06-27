from typing import Annotated
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from base.openapi import generate_responses
from clients.s3.exceptions import FailToGeneratePresignedUrlError
from containers import Container
from docs.exceptions import (
    NotAllowedExtensionError,
)
from .dtos.docs_dto import (
    GetUploadUrlMetadata,
    GetUploadUrlRequest,
    GetUploadUrlResponse,
)
from .services.doc_writer import DocWriter


router = APIRouter(prefix="/api/v1/docs", tags=["docs"])


@router.post(
    "/upload-url",
    response_model=GetUploadUrlResponse,
    responses=generate_responses(
        NotAllowedExtensionError,
        FailToGeneratePresignedUrlError,
    ),
)
@inject
async def get_upload_url(
    request: GetUploadUrlRequest,
    doc_writer: Annotated[DocWriter, Depends(Provide[Container.doc_writer])],
):
    presigned_url = await doc_writer.get_upload_url(request.filename, request.size)

    return GetUploadUrlResponse(
        presignedUrl=presigned_url.url,
        metadata=GetUploadUrlMetadata(doc_id=presigned_url.doc_id),
    )
