import pytest
import uuid
from typing import Dict, Any

from docs.tasks.services.doc_writer import DocWriter

from .fakes import (
    FakeS3Client,
    FakeEsTaskClient,
    FakeDocTaskRepository,
    FakeSession,
    FakeWriteSessionManager,
    FakeIndexHandler,
)

from docs.dtos.docs_dto import IndexDocsParams


@pytest.fixture
def fake_s3_client() -> FakeS3Client:
    return FakeS3Client()


@pytest.fixture
def fake_es_client() -> FakeEsTaskClient:
    return FakeEsTaskClient()


@pytest.fixture
def fake_repo() -> FakeDocTaskRepository:
    return FakeDocTaskRepository()


@pytest.fixture
def fake_session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def fake_session_manager(fake_session: FakeSession) -> FakeWriteSessionManager:
    return FakeWriteSessionManager(session=fake_session)


@pytest.fixture
def fake_index_handler() -> FakeIndexHandler:
    return FakeIndexHandler()


@pytest.fixture
def doc_writer(
    fake_s3_client: FakeS3Client,
    fake_es_client: FakeEsTaskClient,
    fake_session_manager: FakeWriteSessionManager,
    fake_repo: FakeDocTaskRepository,
) -> DocWriter:
    return DocWriter(
        s3_client=fake_s3_client,
        es_client=fake_es_client,
        write_session_manager=fake_session_manager,
        repo=fake_repo,
        bucket_name="test-bucket",
        allowed_extensions=[
            "pptx",
            "docx",
            "pdf",
            "txt",
            "ppt",
            "doc",
            "hwp",
            "hwpx",
            "json",
            "py",
        ],
        doc_size_limit=1000000,
        doc_index_name="test-index",
    )


@pytest.fixture
def doc_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def index_params(doc_id: uuid.UUID) -> IndexDocsParams:
    return IndexDocsParams(
        key=f"test-bucket/docs/{doc_id}.pdf", chunk_size=100, chunk_overlap_ratio=0.1
    )
