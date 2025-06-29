import pytest
import uuid
from pathlib import Path
from datetime import timedelta

from base.date import get_utc_now
from docs.dtos.docs_dto import IndexDocsParams
from docs.exceptions import NotAllowedExtensionError
from docs.models.doc_model import DocStatus, Docs
from docs.tasks.services.doc_writer import DocWriter
from tests.fakes import (
    FakeDocTaskRepository,
    FakeEsTaskClient,
    FakeIndexHandler,
    FakeReader,
    FakeS3Client,
    FakeSession,
)


class TestDocWriterIndexDocs:

    def test_index_docs_success(
        self,
        doc_writer: DocWriter,
        fake_es_client: FakeEsTaskClient,
        fake_repo: FakeDocTaskRepository,
        index_params: IndexDocsParams,
        doc_id: uuid.UUID,
        mocker,
    ):
        # Arrange
        fake_reader = FakeReader()
        mocker.patch.object(doc_writer, "_get_reader", return_value=fake_reader)

        # Act
        doc_writer.index_docs(params=index_params)

        # Assert
        assert fake_es_client.call_count == 1
        assert len(fake_es_client.indexed_docs) > 0
        assert fake_es_client.indexed_docs[0].doc_id == doc_id
        assert fake_es_client.indexed_docs[0].metadata.ext == "pdf"

        last_status_update = fake_repo.status_update_history[-1]
        assert last_status_update["status"] == DocStatus.INDEXED
        assert doc_id in last_status_update["doc_ids"]

    def test_s3_download_failed(
        self,
        doc_writer: DocWriter,
        fake_s3_client: FakeS3Client,
        fake_repo: FakeDocTaskRepository,
        index_params: IndexDocsParams,
        doc_id: uuid.UUID,
    ):
        # Arrange
        fake_s3_client.should_fail = True

        # Act
        doc_writer.index_docs(params=index_params)

        # Assert
        last_status_update = fake_repo.status_update_history[-1]
        assert last_status_update["status"] == DocStatus.DOWNLOAD_FAILED
        assert doc_id in last_status_update["doc_ids"]

    def test_read_failed(
        self,
        doc_writer: DocWriter,
        fake_repo: FakeDocTaskRepository,
        index_params: IndexDocsParams,
        doc_id: uuid.UUID,
        mocker,
    ):
        # Arrange
        fake_reader = FakeReader()
        fake_reader.should_fail = True
        mocker.patch.object(doc_writer, "_get_reader", return_value=fake_reader)

        mock_unlink = mocker.patch.object(Path, "unlink")

        # Act & Assert
        with pytest.raises(Exception, match="Fake reader failed to load data"):
            doc_writer.index_docs(params=index_params)

        # Assert after exception
        last_status_update = fake_repo.status_update_history[-1]
        assert last_status_update["status"] == DocStatus.READ_FAILED
        assert doc_id in last_status_update["doc_ids"]
        mock_unlink.assert_called_once()

    def test_splitting_failed(
        self,
        doc_writer: DocWriter,
        fake_repo: FakeDocTaskRepository,
        index_params: IndexDocsParams,
        doc_id: uuid.UUID,
        mocker,
    ):
        # Arrange
        fake_reader = FakeReader()
        mocker.patch.object(doc_writer, "_get_reader", return_value=fake_reader)

        mocker.patch(
            "llama_index.core.node_parser.SentenceSplitter.get_nodes_from_documents",
            side_effect=Exception("Fake splitting failed"),
        )

        # Act & Assert
        with pytest.raises(Exception, match="Fake splitting failed"):
            doc_writer.index_docs(params=index_params)

        # Assert after exception
        last_status_update = fake_repo.status_update_history[-1]
        assert last_status_update["status"] == DocStatus.SPLITTING_FAILED
        assert doc_id in last_status_update["doc_ids"]

    def test_indexing_failed(
        self,
        doc_writer: DocWriter,
        fake_es_client: FakeEsTaskClient,
        fake_repo: FakeDocTaskRepository,
        index_params: IndexDocsParams,
        doc_id: uuid.UUID,
        mocker,
    ):
        # Arrange
        fake_es_client.should_fail = True
        fake_reader = FakeReader()
        mocker.patch.object(doc_writer, "_get_reader", return_value=fake_reader)

        # Act & Assert
        with pytest.raises(Exception, match="Fake Elasticsearch indexing failed"):
            doc_writer.index_docs(params=index_params)

        # Assert after exception
        last_status_update = fake_repo.status_update_history[-1]
        assert last_status_update["status"] == DocStatus.INDEXING_FAILED
        assert doc_id in last_status_update["doc_ids"]

    def test_not_allowed_extension(self, doc_writer: DocWriter):
        # Arrange
        params_wrong_ext = IndexDocsParams(
            key="tmp/f581f4d4-00e6-4011-9cad-8f86946a3a3c.zip",
            chunk_size=100,
            chunk_overlap_ratio=0.1,
        )

        # Act & Assert
        with pytest.raises(NotAllowedExtensionError):
            doc_writer.index_docs(params=params_wrong_ext)


class TestDocWriterRetryDocs:
    def test_retry_when_no_docs_to_retry(
        self,
        doc_writer: DocWriter,
        fake_repo: FakeDocTaskRepository,
        fake_index_handler: FakeIndexHandler,
    ):
        # Arrange
        # Act
        doc_writer.retry_unhandled_docs(index_handler=fake_index_handler)

        # Assert
        assert fake_index_handler.called is False

    def test_retry_success(
        self,
        doc_writer: DocWriter,
        fake_repo: FakeDocTaskRepository,
        fake_session: FakeSession,
        fake_index_handler: FakeIndexHandler,
    ):
        # Arrange
        now = get_utc_now()
        doc1_id = uuid.uuid4()
        doc2_id = uuid.uuid4()
        fake_repo.docs_db = {
            doc1_id: Docs(
                id=doc1_id,
                bucket="b",
                key="k1",
                status=DocStatus.UPLOADED,
                updated_at=now - timedelta(minutes=20),
            ),
            doc2_id: Docs(
                id=doc2_id,
                bucket="b",
                key="k2",
                status=DocStatus.INDEXING,
                updated_at=now - timedelta(minutes=30),
            ),
        }

        # Act
        doc_writer.retry_unhandled_docs(index_handler=fake_index_handler)

        # Assert
        assert fake_repo.docs_db[doc1_id].status == DocStatus.RETRYING
        assert fake_repo.docs_db[doc2_id].status == DocStatus.RETRYING

        assert fake_session.commit_called is True

        assert fake_index_handler.called is True
        assert len(fake_index_handler.payload) == 2
        assert {"bucket": "b", "key": "k1"} in fake_index_handler.payload
        assert {"bucket": "b", "key": "k2"} in fake_index_handler.payload
