from collections.abc import Sequence
from datetime import timedelta
import uuid
from typing import List
from pathlib import Path

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.readers.base import BaseReader
from llama_index.readers.file import (
    PDFReader,
    DocxReader,
    FlatReader,
    HWPReader,
)
from llama_index.core.readers.json import JSONReader

from base.date import get_utc_now
from clients.s3.exceptions import FailToDownloadError
from clients.s3.s3 import S3Client
from db.db import WriteSessionSyncManager
from docs.dtos.docs_dto import IndexDocsParams
from docs.exceptions import NotAllowedExtensionError
from clients.elasticsearch.schema import DocMetadata, DocSchema
from docs.models.doc_model import DocStatus, Docs
from docs.tasks.clients.es_task import EsTaskClient
from docs.tasks.readers.ppt import PptReader
from docs.tasks.repositories.doc_task_repository import DocTaskRepository
from docs.tasks.types import IndexDocTaskType


class DocWriter:
    def __init__(
        self,
        s3_client: S3Client,
        es_client: EsTaskClient,
        write_session_manager: WriteSessionSyncManager,
        repo: DocTaskRepository,
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

    def index_docs(self, params: IndexDocsParams) -> None:
        doc_id_str, ext = params.key.split("/")[-1].split(".")
        doc_id = uuid.UUID(doc_id_str)

        tmp_path = Path(f"/tmp/{doc_id_str}.{ext}")

        # Download the file from S3 to a temporary path
        try:
            self.s3_client.download_file(
                bucket_name=self.bucket_name,
                key=params.key,
                output_path=tmp_path,
            )
        except FailToDownloadError:
            with self.write_session_manager as write_session:
                self.repo.update_status(
                    write_session, [doc_id], DocStatus.DOWNLOAD_FAILED
                )
            return

        reader = self._get_reader(ext)

        # Read docs
        try:
            document = reader.load_data(tmp_path)
        except Exception as e:
            with self.write_session_manager as write_session:
                self.repo.update_status(write_session, [doc_id], DocStatus.READ_FAILED)

            raise e
        finally:

            if tmp_path.exists():
                tmp_path.unlink()

        # Split document into chunks
        try:
            sentence_splitter = SentenceSplitter(
                chunk_size=params.chunk_size,
                chunk_overlap=int(
                    params.chunk_size * max(params.chunk_overlap_ratio, 0)
                ),
            )
            nodes = sentence_splitter.get_nodes_from_documents(document)
        except Exception as e:
            with self.write_session_manager as write_session:
                self.repo.update_status(
                    write_session, [doc_id], DocStatus.SPLITTING_FAILED
                )

            raise e

        # Generate chunk
        splitted_nodes = [
            DocSchema(
                doc_id=doc_id,
                order=order,
                content=node.get_content(),
                metadata=DocMetadata(ext=ext),
            )
            for order, node in enumerate(nodes, start=1)
        ]

        # Write to Elasticsearch
        try:
            self.es_client.index_docs(splitted_nodes, self.doc_index_name)
        except Exception as e:
            with self.write_session_manager as write_session:
                self.repo.update_status(
                    write_session, [doc_id], DocStatus.INDEXING_FAILED
                )

            raise e

        # Update document status
        with self.write_session_manager as write_session:
            self.repo.update_status(write_session, [doc_id], DocStatus.INDEXED)

    def retry_unhandled_docs(self, index_handler: IndexDocTaskType) -> None:
        now = get_utc_now()
        cutoff_time = now - timedelta(minutes=10)
        target_statuses = [
            DocStatus.UPLOAD_REQUESTED,
            DocStatus.UPLOADED,
            DocStatus.INDEXING,
        ]

        docs: Sequence[Docs] = []
        total_cnt = 0
        size = 10
        with self.write_session_manager as write_session:
            total_cnt = self.repo.fetch_count_by_status(
                statuses=target_statuses,
                session=write_session,
                cutoff_time=cutoff_time,
            )

        if total_cnt == 0:
            return

        for chunk in range(0, total_cnt, size):
            with self.write_session_manager as write_session:
                docs = self.repo.fetch_docs_by_status(
                    statuses=target_statuses,
                    session=write_session,
                    cutoff_time=now,
                    offset=chunk,
                    limit=size,
                )

                # Update status to RETRYING
                self.repo.update_status(
                    session=write_session,
                    doc_ids=[doc.id for doc in docs],
                    status=DocStatus.RETRYING,
                )

                write_session.commit()

                index_handler([{"bucket": doc.bucket, "key": doc.key} for doc in docs])

    def _get_reader(self, ext: str) -> BaseReader:
        self._validate_extension(ext)

        READER_MAP = {
            "pptx": PptReader,
            "docx": DocxReader,
            "pdf": PDFReader,
            "txt": FlatReader,
            "ppt": PptReader,
            "doc": DocxReader,
            "hwp": HWPReader,
            "hwpx": HWPReader,
            "json": JSONReader,
            "py": FlatReader,
        }

        return READER_MAP.get(f"{ext.lower()}", FlatReader)()

    def _validate_extension(self, ext: str):
        if ext not in self.allowed_extensions:
            raise NotAllowedExtensionError()
