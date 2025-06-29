from typing import Any, Dict, List, Protocol

from celery.result import AsyncResult

__all__ = ["IndexDocTaskType"]


class IndexDocTaskType(Protocol):
    def __call__(self, req: List[Dict[str, str]]) -> Any: ...
