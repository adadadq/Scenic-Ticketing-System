import logging
import re
import time

from fastapi import Request


REQUEST_LOGGER_NAME = "scenic_ticket.requests"
UNSAFE_LOG_REQUEST_ID = "[invalid]"
SAFE_LOG_REQUEST_ID_RE = re.compile(r"^(?=.*[A-Za-z])[A-Za-z0-9][A-Za-z0-9._:-]{0,79}$")


def elapsed_ms(start_time: float) -> float:
    return round((time.perf_counter() - start_time) * 1000, 2)


def request_id_for_log(request_id: str) -> str:
    if SAFE_LOG_REQUEST_ID_RE.fullmatch(request_id):
        return request_id
    return UNSAFE_LOG_REQUEST_ID


def log_request_summary(request: Request, status_code: int, duration_ms: float) -> None:
    request_id = request_id_for_log(getattr(request.state, "request_id", ""))
    path = request.url.path
    logger = logging.getLogger(REQUEST_LOGGER_NAME)
    logger.info(
        "http_request method=%s path=%s status_code=%s request_id=%s duration_ms=%.2f",
        request.method,
        path,
        status_code,
        request_id,
        duration_ms,
        extra={
            "http_method": request.method,
            "http_path": path,
            "http_status_code": status_code,
            "request_id": request_id,
            "duration_ms": duration_ms,
        },
    )
