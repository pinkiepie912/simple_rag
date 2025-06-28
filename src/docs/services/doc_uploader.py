import uuid
from typing import List

from clients.elasticsearch.es import EsClient
from clients.s3.dto import PresignedUrlMetadata
from clients.s3.s3 import S3Client
from db.db import WriteSessionManager
from docs.dtos.docs_dto import PresignedUrlDto
from docs.exceptions import DocumentSizeLimitExceededError, NotAllowedExtensionError
from docs.models.doc_model import Docs
from docs.repositories.doc_repository import DocRepository

__all__ = ["DocUploader"]


class DocUploader:
    def __init__(
        self,
        s3_client: S3Client,
        es_client: EsClient,
        write_session_manager: WriteSessionManager,
        repo: DocRepository,
        bucket_name: str,
        allowed_extensions: List[str],
        doc_size_limit: int,
        doc_index_name: str,
    ):
        self.s3_client = s3_client
        self.es_client = es_client
        self.write_session_manager = write_session_manager
        self.repo = repo
        self.bucket_name = bucket_name
        self.allowed_extensions = allowed_extensions
        self.doc_size_limit = doc_size_limit
        self.doc_index_name = doc_index_name

    async def get_upload_url(
        self,
        filename: str,
        size_byte: int,
        expire_sec=300,
        key_prefix="docs",
    ) -> PresignedUrlDto:
        ext = filename.split(".")[-1]
        self._validate_extension(ext)

        if size_byte <= 0 or size_byte > self.doc_size_limit:
            raise DocumentSizeLimitExceededError()

        doc_id = str(uuid.uuid4())
        key = f"{key_prefix}/{doc_id}.{ext}"

        presigned_url = self.s3_client.get_presigned_url(
            bucket_name=self.bucket_name,
            key=key,
            metadata=PresignedUrlMetadata(doc_id=doc_id, origin_filename=filename),
            expire_sec=expire_sec,
        )

        new_doc = Docs.of(
            id=uuid.UUID(doc_id),
            name=filename,
            size=size_byte,
            extension=ext,
        )
        async with self.write_session_manager as write_session:
            self.repo.create_doc(write_session, new_doc)

        return PresignedUrlDto(url=presigned_url, doc_id=doc_id)


    def _validate_extension(self, ext: str):
        if ext not in self.allowed_extensions:
            raise NotAllowedExtensionError()
