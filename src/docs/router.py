from typing import Annotated
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from base.openapi import generate_responses
from clients.s3.exceptions import FailToGeneratePresignedUrlError
from containers import Container
from docs.exceptions import (
    NotAllowedExtensionError,
)
from docs.services.doc_reader import DocReader
from .dtos.docs_dto import (
    GetUploadUrlMetadata,
    GetUploadUrlRequest,
    GetUploadUrlResponse,
    SearchDoc,
    SearchDocsRequest,
    SearchDocsResponse,
)
from .services.doc_uploader import DocUploader


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
    doc_writer: Annotated[DocUploader, Depends(Provide[Container.doc_uploader])],
) -> GetUploadUrlResponse:
    presigned_url = await doc_writer.get_upload_url(request.filename, request.size)

    return GetUploadUrlResponse(
        presignedUrl=presigned_url.url,
        metadata=GetUploadUrlMetadata(doc_id=presigned_url.doc_id),
    )


@router.post("/question", response_model=SearchDocsResponse)
@inject
async def search_docs(
    request: SearchDocsRequest,
    doc_reader: Annotated[DocReader, Depends(Provide[Container.doc_reader])],
) -> SearchDocsResponse:
    docs = await doc_reader.search_docs(
        question=request.question, doc_id=request.doc_id
    )
    return SearchDocsResponse.of(
        docs=[SearchDoc.of(doc_id=doc.doc_id, content=doc.content) for doc in docs]
    )
