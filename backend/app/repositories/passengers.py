from dataclasses import dataclass
from typing import Protocol

from psycopg import errors

from app.core.db import connect_db


@dataclass(frozen=True)
class PassengerTemplateRecord:
    id: int
    owner_visitor_id: int
    passenger_name: str
    id_type: str
    id_number: str
    phone: str


class PassengerTemplateConflictError(Exception):
    pass


class PassengerTemplateRepository(Protocol):
    def list_for_owner(self, owner_visitor_id: int) -> list[PassengerTemplateRecord]:
        ...

    def create(self, owner_visitor_id: int, passenger_name: str, id_type: str, id_number: str, phone: str) -> PassengerTemplateRecord:
        ...

    def update(self, template_id: int, owner_visitor_id: int, passenger_name: str, id_type: str, id_number: str, phone: str) -> PassengerTemplateRecord | None:
        ...

    def delete(self, template_id: int, owner_visitor_id: int) -> bool:
        ...


def passenger_template_from_row(row: dict) -> PassengerTemplateRecord:
    return PassengerTemplateRecord(
        id=row["id"],
        owner_visitor_id=row["owner_visitor_id"],
        passenger_name=row["passenger_name"],
        id_type=row["id_type"],
        id_number=row["id_number"],
        phone=row["phone"],
    )


class PostgresPassengerTemplateRepository:
    def list_for_owner(self, owner_visitor_id: int) -> list[PassengerTemplateRecord]:
        with connect_db() as connection:
            rows = connection.execute(
                """
                SELECT id, owner_visitor_id, passenger_name, id_type, id_number, phone
                FROM visitor_passenger_template
                WHERE owner_visitor_id = %s
                ORDER BY updated_at DESC, id DESC
                """,
                (owner_visitor_id,),
            ).fetchall()
        return [passenger_template_from_row(row) for row in rows]

    def create(self, owner_visitor_id: int, passenger_name: str, id_type: str, id_number: str, phone: str) -> PassengerTemplateRecord:
        try:
            with connect_db() as connection:
                row = connection.execute(
                    """
                    INSERT INTO visitor_passenger_template (
                        owner_visitor_id,
                        passenger_name,
                        id_type,
                        id_number,
                        phone
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, owner_visitor_id, passenger_name, id_type, id_number, phone
                    """,
                    (owner_visitor_id, passenger_name, id_type, id_number, phone),
                ).fetchone()
        except errors.UniqueViolation as exc:
            raise PassengerTemplateConflictError from exc
        return passenger_template_from_row(row)

    def update(self, template_id: int, owner_visitor_id: int, passenger_name: str, id_type: str, id_number: str, phone: str) -> PassengerTemplateRecord | None:
        try:
            with connect_db() as connection:
                row = connection.execute(
                    """
                    UPDATE visitor_passenger_template
                    SET passenger_name = %s,
                        id_type = %s,
                        id_number = %s,
                        phone = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND owner_visitor_id = %s
                    RETURNING id, owner_visitor_id, passenger_name, id_type, id_number, phone
                    """,
                    (passenger_name, id_type, id_number, phone, template_id, owner_visitor_id),
                ).fetchone()
        except errors.UniqueViolation as exc:
            raise PassengerTemplateConflictError from exc
        return passenger_template_from_row(row) if row else None

    def delete(self, template_id: int, owner_visitor_id: int) -> bool:
        with connect_db() as connection:
            cursor = connection.execute(
                """
                DELETE FROM visitor_passenger_template
                WHERE id = %s AND owner_visitor_id = %s
                """,
                (template_id, owner_visitor_id),
            )
        return cursor.rowcount > 0


def get_passenger_template_repository() -> PassengerTemplateRepository:
    return PostgresPassengerTemplateRepository()
