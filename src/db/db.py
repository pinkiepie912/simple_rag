import importlib
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from .model import Base

__all__ = ["ReadSessionManager", "WriteSessionManager", "create_tables"]


class ReadSessionManager:
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self._session_maker = session_maker
        self._session: Optional[AsyncSession] = None

    async def __aenter__(self) -> AsyncSession:
        if self._session is None:
            self._session = self._session_maker()
        return self._session

    async def __aexit__(self, exc_type, exc_value, traceback):
        if not self._session:
            return

        try:
            if exc_type:
                return False
        finally:
            await self._session.close()
            self._session = None


class WriteSessionManager:
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self._session_maker = session_maker
        self._session: Optional[AsyncSession] = None

    async def __aenter__(self) -> AsyncSession:
        if self._session is None:
            self._session = self._session_maker()
        return self._session

    async def __aexit__(self, exc_type, exc_value, traceback):
        if not self._session:
            return

        try:
            if exc_type:
                await self._session.rollback()
                return False
            else:
                await self._session.commit()
        finally:
            await self._session.close()
            self._session = None


def _load_models():
    root_dir = Path(__file__).parent.parent

    for models_dir in root_dir.rglob("models"):
        if not models_dir.is_dir():
            continue

        for model_file in models_dir.glob("*.py"):
            if model_file.name == "__init__.py":
                continue

            relative_path = model_file.relative_to(root_dir)
            module_path = ".".join(relative_path.with_suffix("").parts)

            try:
                importlib.import_module(module_path)
                print(f"Successfully imported: {module_path}")
            except Exception as e:
                print(f"Failed to import {module_path}: {e}")


async def create_tables(engine: AsyncEngine):
    _load_models()

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully or already exist.")
    except Exception as e:
        raise e
