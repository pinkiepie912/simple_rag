import asyncio

from celery import shared_task
from dependency_injector.wiring import Provide, inject
from pydantic import BaseModel

from containers import Container
from docs.dtos.docs_dto import IndexDocsParams
from docs.services.doc_writer import DocWriter


class _IndexDocsRequest(BaseModel):
    bucket: str
    key: str


@shared_task(name="docs.tasks.index_docs")
@inject
def index_docs(
    req: dict,
    doc_writer: DocWriter = Provide[Container.doc_writer],
) -> None:
    request = _IndexDocsRequest(**req)
    params = IndexDocsParams(key=request.key)
    asyncio.run(doc_writer.index_docs(params))
