from typing import TYPE_CHECKING, List
import uuid

from docs.dtos.docs_dto import PresignedUrlDto
from docs.exceptions import (
    DocumentSizeLimitExceededError,
    FailToGeneratePresignedUrlError,
    NotAllowedExtensionError,
)

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

__all__ = ["DocWriter"]


class DocWriter:
    def __init__(
        self,
        s3_client: "S3Client",
        bucket_name: str,
        allowed_extensions: List[str],
        doc_size_limit: int,
    ):
        self._s3_client = s3_client
        self.bucket_name = bucket_name
        self.allowed_extensions = allowed_extensions
        self.doc_size_limit = doc_size_limit

    def get_upload_url(
        self, filename: str, size_byte: int, expireSec=300
    ) -> PresignedUrlDto:
        ext = filename.split(".")[-1]
        if ext not in self.allowed_extensions:
            raise NotAllowedExtensionError()

        if size_byte <= 0 or size_byte > self.doc_size_limit:
            raise DocumentSizeLimitExceededError()

        doc_id = str(uuid.uuid4())
        key = f"docs/{doc_id}.{ext}"

        try:
            presigned_url = self._s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": key,
                    "Metadata": {
                        "docId": doc_id,
                    },
                },
                ExpiresIn=expireSec,
            )
        except Exception as e:
            raise FailToGeneratePresignedUrlError(e)

        # TODO: store doc_id and key in mysql

        return PresignedUrlDto(url=presigned_url, doc_id=doc_id)
