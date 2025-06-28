import uuid
from typing import List
from pathlib import Path

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.readers.base import BaseReader
from llama_index.readers.file import (
    PDFReader,
    PptxReader,
    DocxReader,
    FlatReader,
    HWPReader,
)
from llama_index.core.readers.json import JSONReader

from clients.s3.s3 import S3Client
from db.db import WriteSessionSyncManager
from docs.dtos.docs_dto import IndexDocsParams
from docs.exceptions import NotAllowedExtensionError
from clients.elasticsearch.schema import DocMetadata, DocSchema
from docs.models.doc_model import DocStatus
from docs.tasks.clients.es_task import EsTaskClient
from docs.tasks.repositories.doc_task_repository import DocTaskRepository


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

    def index_docs(self, params: IndexDocsParams):
        doc_id_str, ext = params.key.split("/")[-1].split(".")
        doc_id = uuid.UUID(doc_id_str)

        tmp_path = Path(f"/tmp/{doc_id_str}.{ext}")

        # Download the file from S3 to a temporary path
        self.s3_client.download_file(
            bucket_name=self.bucket_name,
            key=params.key,
            output_path=tmp_path,
        )

        reader = self._get_reader(ext)

        # Read docs
        try:
            document = reader.load_data(tmp_path)
        except Exception as e:
            with self.write_session_manager as write_session:
                self.repo.update_status(write_session, doc_id, DocStatus.FILE_ERROR)

            raise e
        finally:

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
                doc_id=doc_id,
                order=order,
                content=node.get_content(),
                metadata=DocMetadata(ext=ext),
            )
            for order, node in enumerate(nodes, start=1)
        ]

        # Write to Elasticsearch
        self.es_client.index_docs(splitted_nodes, self.doc_index_name)

        # Update document status
        with self.write_session_manager as write_session:
            self.repo.update_status(write_session, doc_id, DocStatus.INDEXED)

    def _get_reader(self, ext: str) -> BaseReader:
        self._validate_extension(ext)

        READER_MAP = {
            "pptx": PptxReader,
            "docx": DocxReader,
            "pdf": PDFReader,
            "txt": FlatReader,
            "ppt": PptxReader,
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
