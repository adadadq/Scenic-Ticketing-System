from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from app.core.client_ip import get_client_ip
from app.core.security import get_admin_device_id


@dataclass(frozen=True)
class AdminAuditContext:
    admin_user_id: int
    operator_username: str
    operator_display_name: str
    request_id: str | None
    source_ip: str | None
    device_id: str | None
    admin_session_id: int | None
    user_agent: str | None


def get_admin_audit_context(request: Request, admin) -> AdminAuditContext:
    user_agent = request.headers.get("user-agent", "").strip()[:512] or None
    return AdminAuditContext(
        admin_user_id=admin.id,
        operator_username=admin.username,
        operator_display_name=admin.display_name,
        request_id=getattr(request.state, "request_id", None),
        source_ip=get_client_ip(request),
        device_id=get_admin_device_id(request),
        admin_session_id=getattr(request.state, "admin_session_id", None),
        user_agent=user_agent,
    )
