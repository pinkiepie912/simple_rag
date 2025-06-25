from typing import TYPE_CHECKING
from pathlib import Path

from clients.s3.dto import PresignedUrlMetadata
from clients.s3.exceptions import FailToDownloadError, FailToGeneratePresignedUrlError

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client as S3


__all__ = ["S3Client"]


class S3Client:
    def __init__(self, s3_client: "S3"):
        self._s3_client = s3_client

    def get_presigned_url(
        self,
        bucket_name: str,
        key: str,
        metadata: PresignedUrlMetadata,
        expire_sec: int = 300,
    ) -> str:
        try:
            presigned_url = self._s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": bucket_name,
                    "Key": key,
                    "Metadata": metadata.model_dump(),
                },
                ExpiresIn=expire_sec,
            )

            return presigned_url
        except Exception:
            raise FailToGeneratePresignedUrlError()

    def download_file(self, bucket_name: str, key: str, output_path: Path) -> Path:
        try:
            self._s3_client.download_file(
                Bucket=bucket_name, Key=key, Filename=str(output_path)
            )
            return output_path
        except Exception:
            raise FailToDownloadError()
