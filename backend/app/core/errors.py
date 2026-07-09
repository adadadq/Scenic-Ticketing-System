from dataclasses import dataclass

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


@dataclass
class AppError(Exception):
    status_code: int
    code: str
    message: str


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def error_response(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    request_id = get_request_id(request)
    return JSONResponse(
        status_code=status_code,
        headers={"x-request-id": request_id} if request_id else None,
        content={
            "success": False,
            "code": code,
            "message": message,
            "request_id": request_id,
        },
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return error_response(request, exc.status_code, exc.code, exc.message)


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code == 404:
        return error_response(request, 404, "NOT_FOUND", "资源不存在")
    return error_response(request, exc.status_code, "HTTP_ERROR", "请求无法处理")


async def validation_error_handler(request: Request, _exc: RequestValidationError) -> JSONResponse:
    return error_response(request, 422, "VALIDATION_ERROR", "请求参数不合法")


async def unhandled_error_handler(request: Request, _exc: Exception) -> JSONResponse:
    return error_response(request, 500, "INTERNAL_SERVER_ERROR", "服务暂时不可用")
