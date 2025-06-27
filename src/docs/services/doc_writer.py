from pathlib import Path
import uuid
from typing import List

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.readers.base import BaseReader
from llama_index.readers.file import (
    PptxReader,
    DocxReader,
    PyMuPDFReader,
    FlatReader,
    HWPReader,
)
from llama_index.core.readers.json import JSONReader
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from clients.elasticsearch.es import EsClient
from clients.s3.dto import PresignedUrlMetadata
from clients.s3.s3 import S3Client
from clients.elasticsearch.schema import DocMetadata, DocSchema
from db.db import WriteSessionManager
from docs.dtos.docs_dto import IndexDocsParams, PresignedUrlDto
from docs.exceptions import DocumentSizeLimitExceededError, NotAllowedExtensionError
from docs.models.doc_model import DocStatus, Docs

__all__ = ["DocWriter"]


class DocWriter:
    def __init__(
        self,
        s3_client: S3Client,
        es_client: EsClient,
        write_session_manager: WriteSessionManager,
        bucket_name: str,
        allowed_extensions: List[str],
        doc_size_limit: int,
    ):
        self.s3_client = s3_client
        self.es_client = es_client
        self.write_session_manager = write_session_manager
        self.bucket_name = bucket_name
        self.allowed_extensions = allowed_extensions
        self.doc_size_limit = doc_size_limit

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
            write_session.add(new_doc)

        return PresignedUrlDto(url=presigned_url, doc_id=doc_id)

    async def index_docs(self, params: IndexDocsParams):
        doc_id, ext = params.key.split("/")[-1].split(".")
        tmp_path = Path(f"/tmp/{params.key.split('/')[-1]}")

        # Download the file from S3 to a temporary path
        self.s3_client.download_file(
            bucket_name=self.bucket_name,
            key=params.key,
            output_path=tmp_path,
        )

        # Get file reader
        ext = tmp_path.suffix.lower()
        reader = self._get_reader(ext)

        # Read docs
        try:
            document = reader.load_data(tmp_path)
        except Exception:
            stmt = (
                update(Docs)
                .where(Docs.id == doc_id)
                .values(status=DocStatus.FILE_ERROR.value)
            )

            async with self.write_session_manager as write_session:
                await write_session.execute(stmt)
            return
        finally:
            # Delete temporary file if it exists
            if tmp_path.exists():
                tmp_path.unlink()

        # Split document into chunks
        sentence_splitter = SentenceSplitter(
            chunk_size=params.chunk_size,
            chunk_overlap=int(params.chunk_size * max(params.chunk_overlap_ratio, 0)),
        )
        nodes = sentence_splitter.get_nodes_from_documents(document)

        # Generate chunk
        splitted_nodes = [
            DocSchema(
                doc_id=uuid.UUID(doc_id),
                order=order,
                content=node.get_content(),
                metadata=DocMetadata(ext=ext),
            )
            for order, node in enumerate(nodes, start=1)
        ]

        # Write to Elasticsearch
        await self.es_client.index_docs(splitted_nodes, params.index_name)

        # Update document status
        stmt = (
            update(Docs).where(Docs.id == doc_id).values(status=DocStatus.INDEXED.value)
        )
        async with self.write_session_manager as write_session:
            await write_session.execute(stmt)

    def _get_reader(self, ext: str) -> BaseReader:
        self._validate_extension(ext)

        READER_MAP = {
            ".pptx": PptxReader,
            ".docx": DocxReader,
            ".pdf": PyMuPDFReader,
            ".txt": FlatReader,
            ".ppt": PptxReader,
            ".doc": DocxReader,
            ".hwp": HWPReader,
            ".hwpx": HWPReader,
            ".json": JSONReader,
            ".py": FlatReader,
        }

        return READER_MAP.get(f".{ext.lower()}", FlatReader)()

    def _validate_extension(self, ext: str):
        if ext not in self.allowed_extensions:
            raise NotAllowedExtensionError()
