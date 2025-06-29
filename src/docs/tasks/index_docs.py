from typing import Dict, List, cast
from celery import Task, shared_task
from dependency_injector.wiring import Provide, inject
from pydantic import BaseModel

from celery_containers import CeleryContainer
from docs.dtos.docs_dto import IndexDocsParams
from docs.tasks.services.doc_writer import DocWriter


class _IndexDocsRequest(BaseModel):
    bucket: str
    key: str


@shared_task(name="docs.tasks.index_docs")
@inject
def index_docs(
    req: dict,
    doc_writer: DocWriter = Provide[CeleryContainer.doc_writer],
) -> None:
    request = _IndexDocsRequest(**req)
    params = IndexDocsParams(key=request.key)

    doc_writer.index_docs(params)


@shared_task(name="docs.tasks.retry_indexing_docs")
@inject
def retry_indexing_docs(
    req: List[Dict[str, str]],
    doc_writer: DocWriter = Provide[CeleryContainer.doc_writer],
) -> None:

    for row in req:
        try:
            request = _IndexDocsRequest(**row)
            doc_writer.index_docs(IndexDocsParams(key=request.key))
        except Exception:
            continue


@shared_task(name="docs.tasks.handle_fail_indexing")
@inject
def handle_fail_indexing(
    doc_writer: DocWriter = Provide[CeleryContainer.doc_writer],
) -> None:
    doc_writer.retry_unhandled_docs(
        lambda req: cast(Task, retry_indexing_docs).delay(req)
    )
