import time
from contextlib import asynccontextmanager

from elasticsearch import AsyncElasticsearch, ConnectionError as ESConnectionError
from fastapi import FastAPI
from pydantic import BaseModel

from base.api_exception import APIException, api_exception_handler
from clients.elasticsearch.schema import DocSchema
from config.config import Config
from containers import Container
from db.db import create_tables
from docs.router import router as docs_router


def create_app() -> FastAPI:
    config = Config()
    container = Container()

    container.config.from_pydantic(config)
    container.wire(modules=["docs.router"])

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        es: AsyncElasticsearch = container._es()
        # Connect to Elasticsearch with retries
        for attempt in range(10):
            try:
                await es.info()
                break
            except ESConnectionError as e:
                print(f"Elasticsearch connection error on attempt {attempt + 1}: {e}")
                time.sleep(5)
                if attempt == 9:
                    raise RuntimeError(
                        "Failed to connect to Elasticsearch after 10 attempts"
                    )

        # Create Elasticsearch index
        es_client = container.es_client()
        await es_client.create_idx(DocSchema, config.ELASTICSEARCH.INDEX)

        write_engine = container._write_db_engine()
        read_engine = container._read_db_engine()

        if config.APP_ENV == "dev":
            await create_tables(write_engine)

        print("FastAPI app Initialized")
        yield

        await write_engine.dispose()
        await read_engine.dispose()
        await es.close()

    app = FastAPI(lifespan=lifespan)
    app.state.container = container
    app.add_exception_handler(APIException, api_exception_handler)

    app.include_router(docs_router)
    print("FastAPI app started")
    return app


app = create_app()


class PingResponse(BaseModel):
    status: str


@app.get("/", response_model=PingResponse)
async def ping() -> dict:
    return {"status": "success"}
