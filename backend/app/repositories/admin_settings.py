from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.core.db import connect_db, transaction


@dataclass(frozen=True)
class AdminSystemSettingLogRecord:
    created_at: datetime
    operator_display_name: str
    operator_username: str
    action: str
    source_ip: str | None


class AdminSystemSettingsRepository(Protocol):
    def get_settings(self) -> tuple[dict[str, str], datetime | None]:
        ...

    def update_settings(
        self,
        values: dict[str, str],
        *,
        admin_user_id: int,
        operator_username: str,
        operator_display_name: str,
        request_id: str | None,
        source_ip: str | None,
        action: str,
        changed_keys: list[str],
    ) -> tuple[dict[str, str], datetime | None]:
        ...

    def list_recent_logs(self, limit: int) -> list[AdminSystemSettingLogRecord]:
        ...


class PostgresAdminSystemSettingsRepository:
    def _ensure_schema(self) -> None:
        with connect_db() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS admin_system_setting (
                    setting_key VARCHAR(64) PRIMARY KEY,
                    setting_value VARCHAR(255) NOT NULL,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS admin_system_setting_audit_log (
                    id BIGSERIAL PRIMARY KEY,
                    changed_keys TEXT NOT NULL,
                    action VARCHAR(255) NOT NULL,
                    operator_admin_user_id BIGINT NOT NULL REFERENCES admin_user(id),
                    operator_username VARCHAR(64) NOT NULL,
                    operator_display_name VARCHAR(100) NOT NULL,
                    request_id VARCHAR(64),
                    source_ip VARCHAR(64),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_admin_system_setting_audit_log_created
                    ON admin_system_setting_audit_log (created_at DESC)
                """
            )

    def get_settings(self) -> tuple[dict[str, str], datetime | None]:
        self._ensure_schema()
        with connect_db() as connection:
            rows = connection.execute(
                """
                SELECT setting_key, setting_value, updated_at
                FROM admin_system_setting
                """
            ).fetchall()
        updated_at = max((row["updated_at"] for row in rows), default=None)
        return {row["setting_key"]: row["setting_value"] for row in rows}, updated_at

    def update_settings(
        self,
        values: dict[str, str],
        *,
        admin_user_id: int,
        operator_username: str,
        operator_display_name: str,
        request_id: str | None,
        source_ip: str | None,
        action: str,
        changed_keys: list[str],
    ) -> tuple[dict[str, str], datetime | None]:
        self._ensure_schema()
        with connect_db() as connection:
            with transaction(connection):
                for key, value in values.items():
                    connection.execute(
                        """
                        INSERT INTO admin_system_setting (setting_key, setting_value, updated_at)
                        VALUES (%s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (setting_key)
                        DO UPDATE SET setting_value = EXCLUDED.setting_value,
                                      updated_at = CURRENT_TIMESTAMP
                        """,
                        (key, value),
                    )
                if changed_keys:
                    connection.execute(
                        """
                        INSERT INTO admin_system_setting_audit_log (
                            changed_keys,
                            action,
                            operator_admin_user_id,
                            operator_username,
                            operator_display_name,
                            request_id,
                            source_ip
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            ",".join(changed_keys),
                            action,
                            admin_user_id,
                            operator_username,
                            operator_display_name,
                            request_id,
                            source_ip,
                        ),
                    )
                rows = connection.execute(
                    """
                    SELECT setting_key, setting_value, updated_at
                    FROM admin_system_setting
                    """
                ).fetchall()
        updated_at = max((row["updated_at"] for row in rows), default=None)
        return {row["setting_key"]: row["setting_value"] for row in rows}, updated_at

    def list_recent_logs(self, limit: int) -> list[AdminSystemSettingLogRecord]:
        self._ensure_schema()
        with connect_db() as connection:
            rows = connection.execute(
                """
                SELECT created_at, operator_display_name, operator_username, action, source_ip
                FROM admin_system_setting_audit_log
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (max(1, min(limit, 20)),),
            ).fetchall()
        return [
            AdminSystemSettingLogRecord(
                created_at=row["created_at"],
                operator_display_name=row["operator_display_name"],
                operator_username=row["operator_username"],
                action=row["action"],
                source_ip=row["source_ip"],
            )
            for row in rows
        ]


def get_admin_system_settings_repository() -> AdminSystemSettingsRepository:
    return PostgresAdminSystemSettingsRepository()
