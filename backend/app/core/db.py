from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Protocol

import psycopg
from psycopg.rows import dict_row

from app.core.config import DatabaseSettings, get_settings


class DbConnection(Protocol):
    def execute(self, query: str, params: object | None = None) -> Any:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...

    def close(self) -> None:
        ...


def connect_db(settings: DatabaseSettings | None = None) -> psycopg.Connection:
    database_settings = settings or get_settings().database
    return psycopg.connect(database_settings.dsn, row_factory=dict_row)


@contextmanager
def transaction(connection: DbConnection) -> Iterator[DbConnection]:
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def ping_database(connection: DbConnection) -> bool:
    cursor = connection.execute("SELECT 1 AS ok")
    row = cursor.fetchone()
    if isinstance(row, dict):
        return row.get("ok") == 1
    return bool(row and row[0] == 1)
