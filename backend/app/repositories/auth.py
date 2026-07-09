from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from psycopg import errors

from app.core.db import connect_db


@dataclass(frozen=True)
class VisitorRecord:
    id: int
    visitor_name: str
    id_type: str
    id_number: str
    phone: str
    visitor_scope: str
    username: str | None = None
    password_hash: str | None = None


@dataclass(frozen=True)
class SessionVisitorRecord:
    session_id: int
    visitor: VisitorRecord
    csrf_token_hash: str
    expires_at: datetime
    revoked_at: datetime | None


@dataclass(frozen=True)
class AdminUserRecord:
    id: int
    username: str
    display_name: str
    password_hash: str
    role: str
    status: str


@dataclass(frozen=True)
class SessionAdminRecord:
    session_id: int
    admin: AdminUserRecord
    csrf_token_hash: str
    expires_at: datetime
    revoked_at: datetime | None


class VisitorConflictError(Exception):
    pass


class AdminConflictError(Exception):
    pass


class AuthRepository(Protocol):
    def find_visitor_by_username(self, username: str) -> VisitorRecord | None:
        ...

    def find_visitor_by_phone(self, phone: str) -> VisitorRecord | None:
        ...

    def find_visitor_by_id_doc(self, id_type: str, id_number: str) -> VisitorRecord | None:
        ...

    def create_temp_visitor(self, phone: str) -> VisitorRecord:
        ...

    def get_or_create_temp_visitor(self, phone: str) -> VisitorRecord:
        ...

    def create_registered_visitor(self, visitor_name: str, id_type: str, id_number: str, phone: str) -> VisitorRecord:
        ...

    def update_registered_visitor(self, visitor_id: int, visitor_name: str, id_type: str, id_number: str, phone: str) -> VisitorRecord:
        ...

    def create_registered_account(self, username: str, password_hash: str, phone: str) -> VisitorRecord:
        ...

    def update_registered_account(self, visitor_id: int, username: str, password_hash: str, phone: str) -> VisitorRecord:
        ...

    def create_session(self, visitor_id: int, session_token_hash: str, csrf_token_hash: str, expires_at: datetime) -> None:
        ...

    def find_admin_by_username(self, username: str) -> AdminUserRecord | None:
        ...

    def update_admin_profile(self, admin_user_id: int, username: str, password_hash: str) -> AdminUserRecord:
        ...

    def create_admin_session(self, admin_user_id: int, session_token_hash: str, csrf_token_hash: str, expires_at: datetime) -> None:
        ...

    def find_session_admin(self, session_token_hash: str, now: datetime) -> SessionAdminRecord | None:
        ...

    def find_session_visitor(self, session_token_hash: str, now: datetime) -> SessionVisitorRecord | None:
        ...

    def revoke_session(self, session_token_hash: str) -> None:
        ...

    def update_session_csrf(self, session_token_hash: str, csrf_token_hash: str, now: datetime) -> None:
        ...

    def touch_session(self, session_id: int) -> None:
        ...


def visitor_from_row(row: dict) -> VisitorRecord:
    return VisitorRecord(
        id=row["id"],
        visitor_name=row["visitor_name"],
        id_type=row["id_type"],
        id_number=row["id_number"],
        phone=row["phone"],
        visitor_scope=row["visitor_scope"],
        username=row.get("username"),
        password_hash=row.get("password_hash"),
    )


def admin_from_row(row: dict) -> AdminUserRecord:
    return AdminUserRecord(
        id=row["id"],
        username=row["username"],
        display_name=row["display_name"],
        password_hash=row["password_hash"],
        role=row["role"],
        status=row["status"],
    )


class PostgresAuthRepository:
    def find_visitor_by_username(self, username: str) -> VisitorRecord | None:
        with connect_db() as connection:
            row = connection.execute(
                """
                SELECT id, visitor_name, id_type, id_number, phone, visitor_scope, username, password_hash
                FROM visitor
                WHERE username = %s
                """,
                (username,),
            ).fetchone()
        return visitor_from_row(row) if row else None

    def find_visitor_by_phone(self, phone: str) -> VisitorRecord | None:
        with connect_db() as connection:
            row = connection.execute(
                """
                SELECT id, visitor_name, id_type, id_number, phone, visitor_scope, username, password_hash
                FROM visitor
                WHERE phone = %s
                """,
                (phone,),
            ).fetchone()
        return visitor_from_row(row) if row else None

    def find_visitor_by_id_doc(self, id_type: str, id_number: str) -> VisitorRecord | None:
        with connect_db() as connection:
            row = connection.execute(
                """
                SELECT id, visitor_name, id_type, id_number, phone, visitor_scope, username, password_hash
                FROM visitor
                WHERE id_type = %s AND id_number = %s
                """,
                (id_type, id_number),
            ).fetchone()
        return visitor_from_row(row) if row else None

    def create_temp_visitor(self, phone: str) -> VisitorRecord:
        temp_name = f"临时游客{phone[-4:]}"
        try:
            with connect_db() as connection:
                row = connection.execute(
                    """
                    INSERT INTO visitor (visitor_name, id_type, id_number, phone, visitor_scope)
                    VALUES (%s, 'TEMP_PHONE', %s, %s, 'TEMP')
                    RETURNING id, visitor_name, id_type, id_number, phone, visitor_scope, username, password_hash
                    """,
                    (temp_name, phone, phone),
                ).fetchone()
        except errors.UniqueViolation as exc:
            raise VisitorConflictError from exc
        return visitor_from_row(row)

    def get_or_create_temp_visitor(self, phone: str) -> VisitorRecord:
        visitor = self.find_visitor_by_phone(phone)
        if visitor:
            return visitor
        try:
            return self.create_temp_visitor(phone)
        except VisitorConflictError:
            visitor = self.find_visitor_by_phone(phone)
            if visitor:
                return visitor
            raise

    def create_registered_visitor(self, visitor_name: str, id_type: str, id_number: str, phone: str) -> VisitorRecord:
        try:
            with connect_db() as connection:
                row = connection.execute(
                    """
                    INSERT INTO visitor (visitor_name, id_type, id_number, phone, visitor_scope)
                    VALUES (%s, %s, %s, %s, 'REGISTERED')
                    RETURNING id, visitor_name, id_type, id_number, phone, visitor_scope, username, password_hash
                    """,
                    (visitor_name, id_type, id_number, phone),
                ).fetchone()
        except errors.UniqueViolation as exc:
            raise VisitorConflictError from exc
        return visitor_from_row(row)

    def update_registered_visitor(self, visitor_id: int, visitor_name: str, id_type: str, id_number: str, phone: str) -> VisitorRecord:
        try:
            with connect_db() as connection:
                row = connection.execute(
                    """
                    UPDATE visitor
                    SET visitor_name = %s,
                        id_type = %s,
                        id_number = %s,
                        phone = %s,
                        visitor_scope = 'REGISTERED',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                      AND (
                        visitor_scope = 'TEMP'
                        OR (visitor_scope = 'REGISTERED' AND id_type = %s AND id_number = %s)
                      )
                    RETURNING id, visitor_name, id_type, id_number, phone, visitor_scope, username, password_hash
                    """,
                    (visitor_name, id_type, id_number, phone, visitor_id, id_type, id_number),
                ).fetchone()
        except errors.UniqueViolation as exc:
            raise VisitorConflictError from exc
        if not row:
            raise VisitorConflictError
        return visitor_from_row(row)

    def create_registered_account(self, username: str, password_hash: str, phone: str) -> VisitorRecord:
        try:
            with connect_db() as connection:
                row = connection.execute(
                    """
                    INSERT INTO visitor (
                        visitor_name,
                        id_type,
                        id_number,
                        phone,
                        visitor_scope,
                        username,
                        password_hash
                    )
                    VALUES (%s, 'ACCOUNT', %s, %s, 'REGISTERED', %s, %s)
                    RETURNING id, visitor_name, id_type, id_number, phone, visitor_scope, username, password_hash
                    """,
                    (username, f"ACCOUNT:{username}", phone, username, password_hash),
                ).fetchone()
        except errors.UniqueViolation as exc:
            raise VisitorConflictError from exc
        return visitor_from_row(row)

    def update_registered_account(self, visitor_id: int, username: str, password_hash: str, phone: str) -> VisitorRecord:
        try:
            with connect_db() as connection:
                row = connection.execute(
                    """
                    UPDATE visitor
                    SET visitor_name = %s,
                        id_type = 'ACCOUNT',
                        id_number = %s,
                        phone = %s,
                        visitor_scope = 'REGISTERED',
                        username = %s,
                        password_hash = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                      AND visitor_scope = 'TEMP'
                    RETURNING id, visitor_name, id_type, id_number, phone, visitor_scope, username, password_hash
                    """,
                    (username, f"ACCOUNT:{username}", phone, username, password_hash, visitor_id),
                ).fetchone()
        except errors.UniqueViolation as exc:
            raise VisitorConflictError from exc
        if not row:
            raise VisitorConflictError
        return visitor_from_row(row)

    def create_session(self, visitor_id: int, session_token_hash: str, csrf_token_hash: str, expires_at: datetime) -> None:
        with connect_db() as connection:
            connection.execute(
                """
                INSERT INTO user_session (
                    session_token_hash,
                    csrf_token_hash,
                    account_type,
                    visitor_id,
                    expires_at,
                    last_seen_at
                )
                VALUES (%s, %s, 'VISITOR', %s, %s, CURRENT_TIMESTAMP)
                """,
                (session_token_hash, csrf_token_hash, visitor_id, expires_at),
            )

    def find_admin_by_username(self, username: str) -> AdminUserRecord | None:
        with connect_db() as connection:
            row = connection.execute(
                """
                SELECT id, username, display_name, password_hash, role, status
                FROM admin_user
                WHERE username = %s
                """,
                (username,),
            ).fetchone()
        return admin_from_row(row) if row else None

    def update_admin_profile(self, admin_user_id: int, username: str, password_hash: str) -> AdminUserRecord:
        try:
            with connect_db() as connection:
                row = connection.execute(
                    """
                    UPDATE admin_user
                    SET username = %s,
                        password_hash = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING id, username, display_name, password_hash, role, status
                    """,
                    (username, password_hash, admin_user_id),
                ).fetchone()
        except errors.UniqueViolation as exc:
            raise AdminConflictError from exc
        if not row:
            raise AdminConflictError
        return admin_from_row(row)

    def create_admin_session(self, admin_user_id: int, session_token_hash: str, csrf_token_hash: str, expires_at: datetime) -> None:
        with connect_db() as connection:
            connection.execute(
                """
                INSERT INTO user_session (
                    session_token_hash,
                    csrf_token_hash,
                    account_type,
                    admin_user_id,
                    expires_at,
                    last_seen_at
                )
                VALUES (%s, %s, 'ADMIN', %s, %s, CURRENT_TIMESTAMP)
                """,
                (session_token_hash, csrf_token_hash, admin_user_id, expires_at),
            )

    def find_session_admin(self, session_token_hash: str, now: datetime) -> SessionAdminRecord | None:
        with connect_db() as connection:
            row = connection.execute(
                """
                SELECT
                    s.id AS session_id,
                    s.csrf_token_hash,
                    s.expires_at,
                    s.revoked_at,
                    a.id,
                    a.username,
                    a.display_name,
                    a.password_hash,
                    a.role,
                    a.status
                FROM user_session s
                JOIN admin_user a ON a.id = s.admin_user_id
                WHERE s.session_token_hash = %s
                  AND s.account_type = 'ADMIN'
                  AND s.revoked_at IS NULL
                  AND s.expires_at > %s
                """,
                (session_token_hash, now),
            ).fetchone()
        if not row:
            return None
        return SessionAdminRecord(
            session_id=row["session_id"],
            admin=admin_from_row(row),
            csrf_token_hash=row["csrf_token_hash"],
            expires_at=row["expires_at"],
            revoked_at=row["revoked_at"],
        )

    def find_session_visitor(self, session_token_hash: str, now: datetime) -> SessionVisitorRecord | None:
        with connect_db() as connection:
            row = connection.execute(
                """
                SELECT
                    s.id AS session_id,
                    s.csrf_token_hash,
                    s.expires_at,
                    s.revoked_at,
                    v.id AS visitor_id,
                    v.visitor_name,
                    v.id_type,
                    v.id_number,
                    v.phone,
                    v.visitor_scope
                FROM user_session s
                JOIN visitor v ON v.id = s.visitor_id
                WHERE s.session_token_hash = %s
                  AND s.account_type = 'VISITOR'
                  AND s.revoked_at IS NULL
                  AND s.expires_at > %s
                """,
                (session_token_hash, now),
            ).fetchone()
        if not row:
            return None
        visitor = VisitorRecord(
            id=row["visitor_id"],
            visitor_name=row["visitor_name"],
            id_type=row["id_type"],
            id_number=row["id_number"],
            phone=row["phone"],
            visitor_scope=row["visitor_scope"],
        )
        return SessionVisitorRecord(
            session_id=row["session_id"],
            visitor=visitor,
            csrf_token_hash=row["csrf_token_hash"],
            expires_at=row["expires_at"],
            revoked_at=row["revoked_at"],
        )

    def revoke_session(self, session_token_hash: str) -> None:
        with connect_db() as connection:
            connection.execute(
                """
                UPDATE user_session
                SET revoked_at = CURRENT_TIMESTAMP
                WHERE session_token_hash = %s AND revoked_at IS NULL
                """,
                (session_token_hash,),
            )

    def update_session_csrf(self, session_token_hash: str, csrf_token_hash: str, now: datetime) -> None:
        with connect_db() as connection:
            connection.execute(
                """
                UPDATE user_session
                SET csrf_token_hash = %s,
                    last_seen_at = CURRENT_TIMESTAMP
                WHERE session_token_hash = %s
                  AND revoked_at IS NULL
                  AND expires_at > %s
                """,
                (csrf_token_hash, session_token_hash, now),
            )

    def touch_session(self, session_id: int) -> None:
        with connect_db() as connection:
            connection.execute(
                """
                UPDATE user_session
                SET last_seen_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (session_id,),
            )


def get_auth_repository() -> AuthRepository:
    return PostgresAuthRepository()
