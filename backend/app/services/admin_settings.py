from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import Depends, Request

from app.core.errors import AppError
from app.repositories.admin_settings import (
    AdminSystemSettingLogRecord,
    AdminSystemSettingsRepository,
    get_admin_system_settings_repository,
)
from app.schemas.admin_settings import (
    AdminSystemSettingLogDTO,
    AdminSystemSettingsDTO,
    AdminSystemSettingsUpdateRequest,
)
from app.services.auth import AdminAuthService, get_admin_auth_service


DEFAULT_ADMIN_SYSTEM_SETTINGS: dict[str, Any] = {
    "scenic_name": "遇龙河景区",
    "service_time_start": "08:30",
    "service_time_end": "18:00",
    "ticket_time_start": "08:30",
    "ticket_time_end": "16:30",
    "check_in_time_start": "09:00",
    "check_in_time_end": "17:30",
    "per_order_limit": 10,
    "session_ttl_minutes": 30,
    "csrf_enabled": True,
    "login_guard_enabled": True,
    "sms_enabled": True,
    "mail_enabled": True,
    "refund_enabled": True,
    "stock_enabled": True,
    "audit_retention_days": 90,
    "last_backup_label": "今天 02:30",
}

SETTING_LABELS = {
    "scenic_name": "景区名称",
    "service_time_start": "客服开始时间",
    "service_time_end": "客服结束时间",
    "ticket_time_start": "售票开始时间",
    "ticket_time_end": "售票结束时间",
    "check_in_time_start": "入园开始时间",
    "check_in_time_end": "入园结束时间",
    "per_order_limit": "每单限购",
    "session_ttl_minutes": "会话有效期",
    "csrf_enabled": "CSRF 校验",
    "login_guard_enabled": "登录保护",
    "sms_enabled": "短信通知",
    "mail_enabled": "邮件通知",
    "refund_enabled": "退款提醒",
    "stock_enabled": "库存预警",
    "audit_retention_days": "审计保留天数",
}

BOOL_KEYS = {"csrf_enabled", "login_guard_enabled", "sms_enabled", "mail_enabled", "refund_enabled", "stock_enabled"}
INT_KEYS = {"per_order_limit", "session_ttl_minutes", "audit_retention_days"}


class AdminSystemSettingsService:
    def __init__(
        self,
        repository: AdminSystemSettingsRepository,
        admin_auth_service: AdminAuthService,
    ):
        self.repository = repository
        self.admin_auth_service = admin_auth_service

    def get_settings(self, request: Request) -> AdminSystemSettingsDTO:
        self.admin_auth_service.current_session_admin(request)
        settings, updated_at = self.repository.get_settings()
        return self.to_dto(settings, updated_at, self.repository.list_recent_logs(3))

    def update_settings(self, payload: AdminSystemSettingsUpdateRequest, request: Request) -> AdminSystemSettingsDTO:
        session_record = self.admin_auth_service.require_super_admin(request)
        current, _updated_at = self.repository.get_settings()
        merged = self.merge_defaults(current)
        patch = payload.model_dump(exclude_none=True)
        normalized_patch = {key: self.serialize_value(key, value) for key, value in patch.items()}
        self.validate_time_ranges({**merged, **patch})
        changed_patch = {
            key: value
            for key, value in normalized_patch.items()
            if self.serialize_value(key, merged[key]) != value
        }
        if changed_patch:
            action = self.describe_changes(changed_patch)
            settings, updated_at = self.repository.update_settings(
                changed_patch,
                admin_user_id=session_record.admin.id,
                operator_username=session_record.admin.username,
                operator_display_name=session_record.admin.display_name,
                request_id=getattr(request.state, "request_id", None),
                source_ip=request.client.host if request.client else None,
                action=action,
                changed_keys=list(changed_patch),
            )
        else:
            settings, updated_at = current, _updated_at
        return self.to_dto(settings, updated_at, self.repository.list_recent_logs(3))

    def to_dto(
        self,
        stored_settings: dict[str, str],
        updated_at: datetime | None,
        logs: list[AdminSystemSettingLogRecord],
    ) -> AdminSystemSettingsDTO:
        settings = self.merge_defaults(stored_settings)
        return AdminSystemSettingsDTO(
            scenic_name=settings["scenic_name"],
            service_time_start=settings["service_time_start"],
            service_time_end=settings["service_time_end"],
            ticket_time_start=settings["ticket_time_start"],
            ticket_time_end=settings["ticket_time_end"],
            check_in_time_start=settings["check_in_time_start"],
            check_in_time_end=settings["check_in_time_end"],
            per_order_limit=settings["per_order_limit"],
            session_ttl_minutes=settings["session_ttl_minutes"],
            csrf_enabled=settings["csrf_enabled"],
            login_guard_enabled=settings["login_guard_enabled"],
            sms_enabled=settings["sms_enabled"],
            mail_enabled=settings["mail_enabled"],
            refund_enabled=settings["refund_enabled"],
            stock_enabled=settings["stock_enabled"],
            audit_retention_days=settings["audit_retention_days"],
            last_backup_label=settings["last_backup_label"],
            updated_at=updated_at,
            recent_logs=[
                AdminSystemSettingLogDTO(
                    created_at=log.created_at,
                    operator_display_name=log.operator_display_name,
                    operator_username=log.operator_username,
                    action=log.action,
                    source_ip=log.source_ip,
                )
                for log in logs
            ],
        )

    def merge_defaults(self, stored_settings: dict[str, str]) -> dict[str, Any]:
        settings = DEFAULT_ADMIN_SYSTEM_SETTINGS.copy()
        for key, value in stored_settings.items():
            if key not in settings:
                continue
            if key in BOOL_KEYS:
                settings[key] = value == "true"
            elif key in INT_KEYS:
                settings[key] = int(value)
            else:
                settings[key] = value
        return settings

    @staticmethod
    def serialize_value(key: str, value: Any) -> str:
        if key in BOOL_KEYS:
            return "true" if bool(value) else "false"
        if key in INT_KEYS:
            return str(int(value))
        return str(value).strip()

    @staticmethod
    def validate_time_ranges(settings: dict[str, Any]) -> None:
        for start_key, end_key in (
            ("service_time_start", "service_time_end"),
            ("ticket_time_start", "ticket_time_end"),
            ("check_in_time_start", "check_in_time_end"),
        ):
            start = datetime.strptime(str(settings[start_key]), "%H:%M").time()
            end = datetime.strptime(str(settings[end_key]), "%H:%M").time()
            if start >= end:
                raise AppError(422, "ADMIN_SETTINGS_INVALID", "时间范围不合法")

    @staticmethod
    def describe_changes(changed_patch: dict[str, str]) -> str:
        labels = [SETTING_LABELS.get(key, key) for key in changed_patch]
        if len(labels) == 1:
            return f"修改了系统配置：{labels[0]}"
        return f"修改了系统配置：{labels[0]}等 {len(labels)} 项"


def get_admin_system_settings_service(
    repository: AdminSystemSettingsRepository = Depends(get_admin_system_settings_repository),
    admin_auth_service: AdminAuthService = Depends(get_admin_auth_service),
) -> AdminSystemSettingsService:
    return AdminSystemSettingsService(repository, admin_auth_service)
