import time
from contextlib import asynccontextmanager

from elasticsearch import Elasticsearch, ConnectionError as ESConnectionError
from fastapi import FastAPI
from pydantic import BaseModel

from base.api_exception import APIException, api_exception_handler
from containers import Container
from docs.router import router as docs_router


def create_app() -> FastAPI:
    container = Container()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        es_client: Elasticsearch = container.es_client()
        for attempt in range(10):
            try:
                es_client.info()
                break
            except ESConnectionError as e:
                print(f"Elasticsearch connection error on attempt {attempt + 1}: {e}")
                time.sleep(5)
                if attempt == 9:
                    raise RuntimeError(
                        "Failed to connect to Elasticsearch after 10 attempts"
                    )
        yield
        app.state.container.shutdown_resources()

    app = FastAPI(lifespan=lifespan)
    app.state.container = container
    app.add_exception_handler(APIException, api_exception_handler)

    app.include_router(docs_router)
    return app


app = create_app()


class PingResponse(BaseModel):
    status: str


@app.get("/", response_model=PingResponse)
async def ping() -> dict:
    return {"status": "success"}
