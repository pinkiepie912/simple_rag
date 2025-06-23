from typing import Dict, Any

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse


class APIException(HTTPException):
    status_code: int = 500
    code: str = "INTERNAL_SERVER_ERROR"
    detail: str = "Internal Server Error"
    description: str = "서버 내부 오류가 발생했습니다."
    example: Dict[str, Any] = {"code": code, "detail": detail}

    def __init__(self, detail: str | None = None, **kwargs):
        final_detail = detail if detail is not None else self.detail
        super().__init__(status_code=self.status_code, detail=final_detail, **kwargs)


def api_exception_handler(_: Request, exc: Exception) -> Response:
    if isinstance(exc, APIException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "detail": exc.detail},
        )

    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_SERVER_ERROR",
            "detail": f"An unexpected error occurred: {str(exc)}",
        },
    )
