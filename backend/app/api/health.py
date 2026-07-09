from collections.abc import Iterator

from fastapi import APIRouter, Depends, Request

from app.core.config import AppSettings, get_settings
from app.core.db import DbConnection, connect_db, ping_database
from app.core.errors import AppError
from app.core.responses import success_response
from app.schemas.common import ApiSuccessDTO
from app.schemas.health import DatabaseHealthDTO, HealthDTO

router = APIRouter(prefix="/api", tags=["health"])


def get_database_connection() -> Iterator[DbConnection]:
    try:
        connection = connect_db()
    except Exception as exc:
        raise AppError(503, "DATABASE_UNAVAILABLE", "数据库暂时不可用") from exc
    try:
        yield connection
    finally:
        connection.close()


@router.get("/health", response_model=ApiSuccessDTO[HealthDTO])
async def get_health(request: Request) -> dict:
    settings: AppSettings = get_settings()
    return success_response(
        request,
        {
            "status": "ok",
            "service": settings.app_name,
            "environment": settings.environment,
        },
    )


@router.get("/health/db", response_model=ApiSuccessDTO[DatabaseHealthDTO])
def get_database_health(
    request: Request,
    connection: DbConnection = Depends(get_database_connection),
) -> dict:
    try:
        database_ok = ping_database(connection)
    except Exception as exc:
        raise AppError(503, "DATABASE_UNAVAILABLE", "数据库暂时不可用") from exc

    if not database_ok:
        raise AppError(503, "DATABASE_UNAVAILABLE", "数据库暂时不可用")

    settings: AppSettings = get_settings()
    return success_response(
        request,
        {
            "status": "ok",
            "database": "ok",
            "service": settings.app_name,
            "environment": settings.environment,
        },
    )
