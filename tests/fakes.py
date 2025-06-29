import uuid
from typing import List, Dict, Any, Sequence
from pathlib import Path
from datetime import datetime

from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document as LlamaDocument

from clients.s3.exceptions import FailToDownloadError
from clients.s3.s3 import S3Client
from db.db import WriteSessionSyncManager
from docs.models.doc_model import DocStatus, Docs
from docs.tasks.clients.es_task import EsTaskClient
from docs.tasks.repositories.doc_task_repository import DocTaskRepository
from clients.elasticsearch.schema import DocSchema


class FakeS3Client(S3Client):
    def __init__(self):
        self.should_fail = False
        self.downloaded_files = {}

    def download_file(self, bucket_name: str, key: str, output_path: Path):
        if self.should_fail:
            raise FailToDownloadError("Fake S3 download failed")
        with open(output_path, "w") as f:
            f.write("fake file content")
        self.downloaded_files[key] = output_path

    def upload_file(self, *args, **kwargs):
        pass

    def delete_file(self, *args, **kwargs):
        pass

    def get_presigned_url(self, *args, **kwargs):
        pass


class FakeEsTaskClient(EsTaskClient):

    def __init__(self):
        self.should_fail = False
        self.indexed_docs: List[DocSchema] = []
        self.call_count = 0

    def index_docs(self, docs: List[DocSchema], index_name: str):
        self.call_count += 1
        if self.should_fail:
            raise Exception("Fake Elasticsearch indexing failed")
        self.indexed_docs.extend(docs)


class FakeSession:
    def __init__(self):
        self.commit_called = False

    def commit(self):
        self.commit_called = True

    def add(self, *args, **kwargs):
        pass


class FakeWriteSessionManager(WriteSessionSyncManager):
    _session: FakeSession

    def __init__(self, session: FakeSession):
        self._session = session

    def __enter__(self):
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class FakeDocTaskRepository(DocTaskRepository):
    def __init__(self):
        self.docs_db: Dict[uuid.UUID, Docs] = {}
        self.status_update_history = []

    def update_status(self, session: Any, doc_ids: List[uuid.UUID], status: DocStatus):
        self.status_update_history.append({"doc_ids": doc_ids, "status": status})
        for doc_id in doc_ids:
            if doc_id in self.docs_db:
                self.docs_db[doc_id].status = status

    def fetch_count_by_status(
        self, statuses: List[DocStatus], session: Any, cutoff_time: datetime
    ) -> int:
        count = 0
        for doc in self.docs_db.values():
            if doc.status in statuses and doc.updated_at < cutoff_time:
                count += 1
        return count

    def fetch_docs_by_status(
        self,
        statuses: List[DocStatus],
        session: Any,
        cutoff_time: datetime,
        offset: int,
        limit: int,
    ) -> Sequence[Docs]:
        filtered_docs = []
        for doc in self.docs_db.values():
            if doc.status in statuses and doc.updated_at < cutoff_time:
                filtered_docs.append(doc)
        return filtered_docs[offset : offset + limit]


class FakeReader(BaseReader):
    def __init__(self):
        self.should_fail = False

    def load_data(self, file: Path, **kwargs) -> List[LlamaDocument]:
        if self.should_fail:
            raise Exception("Fake reader failed to load data")
        return [LlamaDocument(text="This is a sentence from a fake document.")]


class FakeIndexHandler:
    def __init__(self):
        self.called = False
        self.payload = None

    def __call__(self, payload: List[Dict[str, str]]):
        self.called = True
        self.payload = payload
