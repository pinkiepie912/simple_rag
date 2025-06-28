from celery import shared_task
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
