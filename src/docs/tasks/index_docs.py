from celery import shared_task
from dependency_injector.wiring import Provide, inject
from pydantic import BaseModel

from config.config import Config
from containers import Container
from docs.dtos.docs_dto import IndexDocsParams
from docs.services.doc_writer import DocWriter


class _IndexDocsRequest(BaseModel):
    bucket: str
    key: str


@shared_task(name="docs.tasks.index_docs")
@inject
async def index_docs(
    req: _IndexDocsRequest,
    doc_writer: DocWriter = Provide[Container.doc_writer],
    config: Config = Provide[Container.config],
) -> None:
    params = IndexDocsParams(index_name=config.S3.DOCS_BUCKET, key=req.key)
    await doc_writer.index_docs(params)
