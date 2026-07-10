from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from app.core.db import connect_db
from app.core.responses import success_response
from app.schemas.common import ApiSuccessDTO
from app.services.auth import AdminAuthService, get_admin_auth_service

router = APIRouter(prefix="/api/admin/audit-logs", tags=["admin-audit-logs"])


class AdminAuditLogDTO(BaseModel):
    id: str
    created_at: datetime = Field(alias="createdAt")
    operator_display_name: str = Field(alias="operatorDisplayName")
    operator_username: str = Field(alias="operatorUsername")
    type: Literal["系统设置", "票种管理", "核验入园", "核验失败", "发起退款"]
    object: str
    result: Literal["成功", "警告"]
    action: str
    request_id: str | None = Field(default=None, alias="requestId")
    source_ip: str | None = Field(default=None, alias="sourceIp")
    device_id: str | None = Field(default=None, alias="deviceId")
    admin_session_id: int | None = Field(default=None, alias="adminSessionId")
    user_agent: str | None = Field(default=None, alias="userAgent")

    model_config = ConfigDict(populate_by_name=True)


class AdminAuditLogListDTO(BaseModel):
    items: list[AdminAuditLogDTO]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")

    model_config = ConfigDict(populate_by_name=True)


@router.get("", response_model=ApiSuccessDTO[AdminAuditLogListDTO])
def list_admin_audit_logs(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    admin_auth_service: AdminAuthService = Depends(get_admin_auth_service),
) -> dict:
    admin_auth_service.current_session_admin(request)
    limit = page_size
    offset = (page - 1) * page_size
    with connect_db() as connection:
        count_row = connection.execute(
            """
            SELECT CAST(SUM(row_count) AS INTEGER) AS total
            FROM (
                SELECT COUNT(*) AS row_count FROM admin_system_setting_audit_log
                UNION ALL SELECT COUNT(*) AS row_count FROM admin_ticket_audit_log
                UNION ALL SELECT COUNT(*) AS row_count FROM check_in_audit_log
                UNION ALL SELECT COUNT(*) AS row_count FROM check_in_failure_audit_log
                UNION ALL SELECT COUNT(*) AS row_count FROM refund_audit_log
            ) audit_counts
            """
        ).fetchone()
        rows = connection.execute(
            """
            SELECT *
            FROM (
                SELECT
                    'SETTING-' || CAST(id AS VARCHAR) AS id,
                    created_at,
                    operator_display_name,
                    operator_username,
                    '系统设置' AS type,
                    '系统设置' AS object,
                    '成功' AS result,
                    action,
                    request_id,
                    source_ip,
                    device_id,
                    admin_session_id,
                    user_agent
                FROM admin_system_setting_audit_log
                UNION ALL
                SELECT
                    'TICKET-' || CAST(id AS VARCHAR) AS id,
                    created_at,
                    operator_display_name,
                    operator_username,
                    '票种管理' AS type,
                    ticket_name AS object,
                    '成功' AS result,
                    CASE action
                        WHEN 'CREATE' THEN '新增票种'
                        WHEN 'DELETE' THEN '删除票种'
                        ELSE '修改票种'
                    END AS action,
                    request_id,
                    source_ip,
                    device_id,
                    admin_session_id,
                    user_agent
                FROM admin_ticket_audit_log
                UNION ALL
                SELECT
                    'CHECKIN-' || CAST(id AS VARCHAR) AS id,
                    created_at,
                    operator_display_name,
                    operator_username,
                    '核验入园' AS type,
                    ticket_code AS object,
                    '成功' AS result,
                    CASE action WHEN 'UNDO_CHECK_IN' THEN '撤销核验' ELSE '核验入园' END AS action,
                    request_id,
                    source_ip,
                    device_id,
                    admin_session_id,
                    user_agent
                FROM check_in_audit_log
                UNION ALL
                SELECT
                    'CHECKINFAIL-' || CAST(id AS VARCHAR) AS id,
                    created_at,
                    operator_display_name,
                    operator_username,
                    '核验失败' AS type,
                    ticket_code AS object,
                    '警告' AS result,
                    failure_message AS action,
                    request_id,
                    source_ip,
                    device_id,
                    admin_session_id,
                    user_agent
                FROM check_in_failure_audit_log
                UNION ALL
                SELECT
                    'REFUND-' || CAST(id AS VARCHAR) AS id,
                    created_at,
                    operator_display_name,
                    operator_username,
                    '发起退款' AS type,
                    order_no AS object,
                    '成功' AS result,
                    CASE refund_type WHEN 'PARTIAL' THEN '部分退款' ELSE '整单退款' END AS action,
                    request_id,
                    source_ip,
                    device_id,
                    admin_session_id,
                    user_agent
                FROM refund_audit_log
            ) audit_logs
            ORDER BY created_at DESC, id DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        ).fetchall()
    data = AdminAuditLogListDTO(
        items=[AdminAuditLogDTO(**row) for row in rows],
        total=count_row["total"] if count_row else 0,
        page=page,
        page_size=page_size,
    )
    return success_response(request, data.model_dump(by_alias=True, mode="json"))
