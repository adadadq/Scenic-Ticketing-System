import csv
import io
import zipfile
from datetime import UTC, date, datetime
from xml.etree import ElementTree

import pytest
from fastapi.testclient import TestClient

import app.repositories.orders as order_repository_module
import app.services.orders as order_service_module
from app.core.errors import AppError
from app.main import create_app
from app.repositories.auth import get_auth_repository
from app.repositories.orders import (
    AdminCheckInAuditInput,
    AdminCheckInFailureAuditLogExportFilter,
    AdminCheckInFailureAuditLogListFilter,
    AdminCheckInFailureAuditLogListRecord,
    AdminCheckInFailureAuditLogRecord,
    AdminCheckInAuditLogExportFilter,
    AdminCheckInAuditLogRecord,
    AdminCheckInAuditLogListFilter,
    AdminCheckInAuditLogListRecord,
    AdminCheckInRecord,
    AdminUndoCheckInRecord,
    PostgresOrderRepository,
    TicketAlreadyCheckedInError,
    TicketNotCheckableError,
    TicketNotCheckedInError,
    TicketUndoNotAllowedError,
    get_order_repository,
)
from app.services.orders import AdminCheckInService, SYNC_EXPORT_ROW_LIMIT

from test_admin_auth_api import FakeAuthRepository, admin_login_payload, seed_enabled_admin
from test_auth_api import csrf_headers


EXPORT_FETCH_LIMIT = SYNC_EXPORT_ROW_LIMIT + 1


class FakeCheckInRepository:
    def __init__(self):
        self.checked_in_count = 0
        self.quota_update_should_fail = False
        self.records: dict[str, AdminCheckInRecord] = {
            "TK-UNUSED": AdminCheckInRecord(
                order_no="O-PAID",
                item_no="I-UNUSED",
                ticket_code="TK-UNUSED",
                order_status="PAID",
                item_status="UNUSED",
                checked_in_at=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
            ),
            "TK-USED": AdminCheckInRecord(
                order_no="O-PAID",
                item_no="I-USED",
                ticket_code="TK-USED",
                order_status="COMPLETED",
                item_status="USED",
                checked_in_at=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
            ),
            "TK-USED-UNPAID": AdminCheckInRecord(
                order_no="O-UNPAID",
                item_no="I-USED-UNPAID",
                ticket_code="TK-USED-UNPAID",
                order_status="PAID",
                item_status="USED",
                checked_in_at=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
            ),
            "TK-CANCELLED": AdminCheckInRecord(
                order_no="O-CANCELLED",
                item_no="I-CANCELLED",
                ticket_code="TK-CANCELLED",
                order_status="CANCELLED",
                item_status="CANCELLED",
                checked_in_at=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
            ),
            "TK-USED-CANCELLED": AdminCheckInRecord(
                order_no="O-CANCELLED",
                item_no="I-USED-CANCELLED",
                ticket_code="TK-USED-CANCELLED",
                order_status="CANCELLED",
                item_status="USED",
                checked_in_at=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
            ),
            "TK-UNPAID": AdminCheckInRecord(
                order_no="O-UNPAID",
                item_no="I-UNPAID",
                ticket_code="TK-UNPAID",
                order_status="PAID",
                item_status="UNUSED",
                checked_in_at=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
            ),
            "TK-REFUNDED": AdminCheckInRecord(
                order_no="O-REFUNDED",
                item_no="I-REFUNDED",
                ticket_code="TK-REFUNDED",
                order_status="REFUNDED",
                item_status="REFUNDED",
                checked_in_at=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
            ),
            "TK-PARTIAL": AdminCheckInRecord(
                order_no="O-PARTIAL",
                item_no="I-PARTIAL-UNUSED",
                ticket_code="TK-PARTIAL",
                order_status="PAID",
                item_status="UNUSED",
                checked_in_at=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
            ),
        }
        self.payment_statuses = {
            "TK-UNUSED": "PAID",
            "TK-USED": "PAID",
            "TK-USED-UNPAID": "UNPAID",
            "TK-CANCELLED": "UNPAID",
            "TK-USED-CANCELLED": "PAID",
            "TK-UNPAID": "UNPAID",
            "TK-REFUNDED": "REFUNDED",
            "TK-PARTIAL": "PARTIAL_REFUND",
        }
        self.audit_logs: dict[str, list[AdminCheckInAuditLogRecord]] = {ticket_code: [] for ticket_code in self.records}
        self.failure_audit_logs: list[AdminCheckInFailureAuditLogRecord] = []
        self.last_failure_audit_log_filters: AdminCheckInFailureAuditLogListFilter | None = None
        self.last_failure_audit_log_export_filters: AdminCheckInFailureAuditLogExportFilter | None = None
        self.last_export_filters: AdminCheckInAuditLogExportFilter | None = None
        self.undo_count = 0

    def check_in_ticket(self, ticket_code: str, audit: AdminCheckInAuditInput) -> AdminCheckInRecord | None:
        if ticket_code == "TK-SYSTEM-ERROR":
            raise AppError(503, "CHECK_IN_UPSTREAM_UNAVAILABLE", "核销服务暂时不可用")
        record = self.records.get(ticket_code)
        if record is None:
            return None
        if record.item_status == "USED":
            raise TicketAlreadyCheckedInError
        if self.quota_update_should_fail:
            raise TicketNotCheckableError
        if (
            record.item_status != "UNUSED"
            or record.order_status != "PAID"
            or self.payment_statuses[ticket_code] not in ("PAID", "PARTIAL_REFUND")
        ):
            raise TicketNotCheckableError

        self.checked_in_count += 1
        checked = AdminCheckInRecord(
            order_no=record.order_no,
            item_no=record.item_no,
            ticket_code=record.ticket_code,
            order_status="COMPLETED",
            item_status="USED",
            checked_in_at=datetime(2026, 7, 1, 10, 30, tzinfo=UTC),
        )
        self.records[ticket_code] = checked
        self.audit_logs[ticket_code].insert(
            0,
            AdminCheckInAuditLogRecord(
                order_no=checked.order_no,
                item_no=checked.item_no,
                ticket_code=checked.ticket_code,
                action="CHECK_IN",
                operator_username=audit.operator_username,
                operator_display_name=audit.operator_display_name,
                request_id=audit.request_id,
                created_at=checked.checked_in_at,
                reason=None,
            ),
        )
        return checked

    def undo_check_in_ticket(self, ticket_code: str, audit: AdminCheckInAuditInput) -> AdminUndoCheckInRecord | None:
        if ticket_code == "TK-SYSTEM-ERROR":
            raise AppError(503, "CHECK_IN_UPSTREAM_UNAVAILABLE", "核销服务暂时不可用")
        record = self.records.get(ticket_code)
        if record is None:
            return None
        if record.item_status != "USED":
            raise TicketNotCheckedInError
        if record.order_status not in ("PAID", "COMPLETED") or self.payment_statuses[ticket_code] not in (
            "PAID",
            "PARTIAL_REFUND",
        ):
            raise TicketUndoNotAllowedError

        self.undo_count += 1
        undone = AdminUndoCheckInRecord(
            order_no=record.order_no,
            item_no=record.item_no,
            ticket_code=record.ticket_code,
            order_status="PAID",
            item_status="UNUSED",
            undone_at=datetime(2026, 7, 1, 11, 0, tzinfo=UTC),
        )
        self.records[ticket_code] = AdminCheckInRecord(
            order_no=undone.order_no,
            item_no=undone.item_no,
            ticket_code=undone.ticket_code,
            order_status=undone.order_status,
            item_status=undone.item_status,
            checked_in_at=undone.undone_at,
        )
        self.audit_logs[ticket_code].insert(
            0,
            AdminCheckInAuditLogRecord(
                order_no=undone.order_no,
                item_no=undone.item_no,
                ticket_code=undone.ticket_code,
                action="UNDO_CHECK_IN",
                operator_username=audit.operator_username,
                operator_display_name=audit.operator_display_name,
                request_id=audit.request_id,
                created_at=undone.undone_at,
                reason=audit.reason,
            ),
        )
        return undone

    def list_check_in_audit_logs(self, ticket_code: str) -> list[AdminCheckInAuditLogRecord] | None:
        if ticket_code not in self.records:
            return None
        return self.audit_logs[ticket_code]

    def list_check_in_audit_log_entries(
        self,
        filters: AdminCheckInAuditLogListFilter,
    ) -> AdminCheckInAuditLogListRecord:
        logs = [log for ticket_logs in self.audit_logs.values() for log in ticket_logs]
        if filters.ticket_code:
            logs = [log for log in logs if filters.ticket_code.upper() in log.ticket_code.upper()]
        if filters.order_no:
            logs = [log for log in logs if filters.order_no.upper() in log.order_no.upper()]
        if filters.operator_username:
            logs = [log for log in logs if filters.operator_username.upper() in log.operator_username.upper()]
        if filters.reason:
            logs = [log for log in logs if log.reason and filters.reason.upper() in log.reason.upper()]
        if filters.date_from:
            logs = [log for log in logs if log.created_at.date() >= filters.date_from]
        if filters.date_to:
            logs = [log for log in logs if log.created_at.date() <= filters.date_to]
        logs = sorted(logs, key=lambda log: log.created_at, reverse=True)
        total = len(logs)
        offset = (filters.page - 1) * filters.page_size
        return AdminCheckInAuditLogListRecord(
            items=logs[offset : offset + filters.page_size],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )

    def record_check_in_failure_audit_log(
        self,
        ticket_code: str,
        action: str,
        failure_code: str,
        failure_message: str,
        audit: AdminCheckInAuditInput,
    ) -> None:
        self.failure_audit_logs.insert(
            0,
            AdminCheckInFailureAuditLogRecord(
                ticket_code=ticket_code,
                action=action,
                failure_code=failure_code,
                failure_message=failure_message,
                operator_username=audit.operator_username,
                operator_display_name=audit.operator_display_name,
                request_id=audit.request_id,
                created_at=datetime(2026, 7, 1, 12, len(self.failure_audit_logs), tzinfo=UTC),
            ),
        )

    def list_check_in_failure_audit_log_entries(
        self,
        filters: AdminCheckInFailureAuditLogListFilter,
    ) -> AdminCheckInFailureAuditLogListRecord:
        self.last_failure_audit_log_filters = filters
        logs = self._filter_failure_audit_logs(filters)
        total = len(logs)
        start = (filters.page - 1) * filters.page_size
        end = start + filters.page_size
        return AdminCheckInFailureAuditLogListRecord(
            items=logs[start:end],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )

    def list_check_in_failure_audit_log_export_rows(
        self,
        filters: AdminCheckInFailureAuditLogExportFilter,
    ) -> list[AdminCheckInFailureAuditLogRecord]:
        self.last_failure_audit_log_export_filters = filters
        return self._filter_failure_audit_logs(filters)

    def _filter_failure_audit_logs(
        self,
        filters: AdminCheckInFailureAuditLogListFilter | AdminCheckInFailureAuditLogExportFilter,
    ) -> list[AdminCheckInFailureAuditLogRecord]:
        logs = list(self.failure_audit_logs)
        if filters.ticket_code:
            logs = [log for log in logs if filters.ticket_code.upper() in log.ticket_code.upper()]
        if filters.failure_code:
            logs = [log for log in logs if log.failure_code == filters.failure_code]
        if filters.operator_username:
            logs = [log for log in logs if filters.operator_username.upper() in log.operator_username.upper()]
        if filters.date_from:
            logs = [log for log in logs if log.created_at.date() >= filters.date_from]
        if filters.date_to:
            logs = [log for log in logs if log.created_at.date() <= filters.date_to]
        return logs

    def list_check_in_audit_log_export_rows(
        self,
        filters: AdminCheckInAuditLogExportFilter,
    ) -> list[AdminCheckInAuditLogRecord]:
        self.last_export_filters = filters
        return self.list_check_in_audit_log_entries(
            AdminCheckInAuditLogListFilter(
                ticket_code=filters.ticket_code,
                order_no=filters.order_no,
                operator_username=filters.operator_username,
                reason=filters.reason,
                date_from=filters.date_from,
                date_to=filters.date_to,
                page=1,
                page_size=1000,
            )
        ).items


def build_client(auth_repo: FakeAuthRepository, check_in_repo: FakeCheckInRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repo
    app.dependency_overrides[get_order_repository] = lambda: check_in_repo
    return TestClient(app)


def login_admin(client: TestClient, auth_repo: FakeAuthRepository) -> dict[str, str]:
    seed_enabled_admin(auth_repo)
    headers = csrf_headers(client)
    response = client.post("/api/admin/auth/login", json=admin_login_payload(), headers=headers)
    assert response.status_code == 200
    return headers


def login_visitor(client: TestClient) -> dict[str, str]:
    headers = csrf_headers(client)
    response = client.post("/api/auth/visitor/register", json={"username": "demo_visitor", "password": "Visitor123", "phone": "13911112222"}, headers=headers)
    assert response.status_code == 200
    return headers


def check_in_audit_input(reason: str | None = None) -> AdminCheckInAuditInput:
    return AdminCheckInAuditInput(
        operator_admin_user_id=1,
        operator_username="demo_admin",
        operator_display_name="演示管理员",
        request_id="req-test",
        reason=reason,
    )


def csv_rows(response_text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(response_text.lstrip("\ufeff"))))


def xlsx_rows(response_content: bytes) -> list[list[str]]:
    with zipfile.ZipFile(io.BytesIO(response_content)) as workbook:
        assert "[Content_Types].xml" in workbook.namelist()
        assert "xl/workbook.xml" in workbook.namelist()
        assert "xl/worksheets/sheet1.xml" in workbook.namelist()
        worksheet_xml = workbook.read("xl/worksheets/sheet1.xml")

    root = ElementTree.fromstring(worksheet_xml)
    namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    assert root.findall(".//x:f", namespace) == []
    rows = []
    for row in root.findall(".//x:row", namespace):
        cells = row.findall("x:c", namespace)
        assert all(cell.attrib["t"] == "inlineStr" for cell in cells)
        rows.append([cell.findtext("x:is/x:t", default="", namespaces=namespace) for cell in cells])
    return rows


def xlsx_worksheet_text(response_content: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(response_content)) as workbook:
        return workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")


def test_admin_can_check_in_unused_ticket_and_complete_order():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    response = client.post("/api/admin/check-ins", json={"ticketCode": "TK-UNUSED"}, headers=headers)

    assert response.status_code == 200
    assert response.json()["data"] == {
        "orderNo": "O-PAID",
        "itemNo": "I-UNUSED",
        "ticketCode": "TK-UNUSED",
        "orderStatus": "COMPLETED",
        "itemStatus": "USED",
        "checkedInAt": "2026-07-01T10:30:00Z",
    }
    assert check_in_repo.checked_in_count == 1
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()


def test_admin_can_batch_check_in_with_per_ticket_business_results():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    response = client.post(
        "/api/admin/check-ins/batch",
        json={"ticketCodes": ["TK-UNUSED", "TK-USED", "TK-MISSING"]},
        headers=headers | {"x-request-id": "req-batch-check-in"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "totalCount": 3,
        "successCount": 1,
        "failureCount": 2,
        "results": [
            {
                "ticketCode": "TK-UNUSED",
                "success": True,
                "checkIn": {
                    "orderNo": "O-PAID",
                    "itemNo": "I-UNUSED",
                    "ticketCode": "TK-UNUSED",
                    "orderStatus": "COMPLETED",
                    "itemStatus": "USED",
                    "checkedInAt": "2026-07-01T10:30:00Z",
                },
            },
            {
                "ticketCode": "TK-USED",
                "success": False,
                "code": "TICKET_ALREADY_USED",
                "message": "票码已核销",
            },
            {
                "ticketCode": "TK-MISSING",
                "success": False,
                "code": "TICKET_NOT_FOUND",
                "message": "票码不存在",
            },
        ],
    }
    assert check_in_repo.checked_in_count == 1
    assert check_in_repo.audit_logs["TK-UNUSED"][0].request_id == "req-batch-check-in"
    assert check_in_repo.audit_logs["TK-USED"] == []
    assert [(log.ticket_code, log.failure_code, log.request_id) for log in check_in_repo.failure_audit_logs] == [
        ("TK-MISSING", "TICKET_NOT_FOUND", "req-batch-check-in"),
        ("TK-USED", "TICKET_ALREADY_USED", "req-batch-check-in"),
    ]
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()
    assert "adminUserId" not in response.text
    assert "sql" not in response.text.lower()


def test_failed_single_check_in_writes_failure_audit_log():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    missing = client.post(
        "/api/admin/check-ins",
        json={"ticketCode": " TK-MISSING "},
        headers=headers | {"x-request-id": "req-missing-check-in"},
    )
    already_used = client.post(
        "/api/admin/check-ins",
        json={"ticketCode": "TK-USED"},
        headers=headers | {"x-request-id": "req-used-check-in"},
    )
    not_checkable = client.post(
        "/api/admin/check-ins",
        json={"ticketCode": "TK-UNPAID"},
        headers=headers | {"x-request-id": "req-unpaid-check-in"},
    )

    assert missing.status_code == 404
    assert missing.json()["code"] == "TICKET_NOT_FOUND"
    assert already_used.status_code == 409
    assert already_used.json()["code"] == "TICKET_ALREADY_USED"
    assert not_checkable.status_code == 409
    assert not_checkable.json()["code"] == "TICKET_NOT_CHECKABLE"
    assert [(log.ticket_code, log.failure_code, log.failure_message, log.request_id) for log in check_in_repo.failure_audit_logs] == [
        ("TK-UNPAID", "TICKET_NOT_CHECKABLE", "当前票码不可核销", "req-unpaid-check-in"),
        ("TK-USED", "TICKET_ALREADY_USED", "票码已核销", "req-used-check-in"),
        ("TK-MISSING", "TICKET_NOT_FOUND", "票码不存在", "req-missing-check-in"),
    ]


def test_admin_can_undo_checked_in_ticket_and_write_audit_log():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    response = client.post(
        "/api/admin/check-ins/TK-USED/undo",
        json={"reason": " 现场误核销 "},
        headers=headers | {"x-request-id": "req-undo-check-in"},
    )
    logs = client.get("/api/admin/check-ins/TK-USED/logs")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "orderNo": "O-PAID",
        "itemNo": "I-USED",
        "ticketCode": "TK-USED",
        "orderStatus": "PAID",
        "itemStatus": "UNUSED",
        "undoneAt": "2026-07-01T11:00:00Z",
    }
    assert check_in_repo.undo_count == 1
    assert logs.status_code == 200
    assert logs.json()["data"][0] == {
        "orderNo": "O-PAID",
        "itemNo": "I-USED",
        "ticketCode": "TK-USED",
        "action": "UNDO_CHECK_IN",
        "reason": "现场误核销",
        "operatorUsername": "admin",
        "operatorDisplayName": "演示管理员",
        "requestId": "req-undo-check-in",
        "createdAt": "2026-07-01T11:00:00Z",
    }
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()


def test_admin_can_batch_undo_check_in_with_per_ticket_business_results():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    response = client.post(
        "/api/admin/check-ins/batch/undo",
        json={
            "ticketCodes": ["TK-USED", "TK-UNUSED", "TK-USED-UNPAID", "TK-MISSING"],
            "reason": "批量误核销",
        },
        headers=headers | {"x-request-id": "req-batch-undo-check-in"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "totalCount": 4,
        "successCount": 1,
        "failureCount": 3,
        "results": [
            {
                "ticketCode": "TK-USED",
                "success": True,
                "undoCheckIn": {
                    "orderNo": "O-PAID",
                    "itemNo": "I-USED",
                    "ticketCode": "TK-USED",
                    "orderStatus": "PAID",
                    "itemStatus": "UNUSED",
                    "undoneAt": "2026-07-01T11:00:00Z",
                },
            },
            {
                "ticketCode": "TK-UNUSED",
                "success": False,
                "code": "TICKET_NOT_CHECKED_IN",
                "message": "票码未核销",
            },
            {
                "ticketCode": "TK-USED-UNPAID",
                "success": False,
                "code": "TICKET_UNDO_NOT_ALLOWED",
                "message": "当前票码不可撤销核销",
            },
            {
                "ticketCode": "TK-MISSING",
                "success": False,
                "code": "TICKET_NOT_FOUND",
                "message": "票码不存在",
            },
        ],
    }
    assert check_in_repo.undo_count == 1
    assert check_in_repo.audit_logs["TK-USED"][0].request_id == "req-batch-undo-check-in"
    assert check_in_repo.audit_logs["TK-USED"][0].reason == "批量误核销"
    assert check_in_repo.audit_logs["TK-UNUSED"] == []
    assert check_in_repo.audit_logs["TK-USED-UNPAID"] == []
    assert [
        (log.ticket_code, log.action, log.failure_code, log.request_id)
        for log in check_in_repo.failure_audit_logs
    ] == [
        ("TK-MISSING", "UNDO_CHECK_IN", "TICKET_NOT_FOUND", "req-batch-undo-check-in"),
        ("TK-USED-UNPAID", "UNDO_CHECK_IN", "TICKET_UNDO_NOT_ALLOWED", "req-batch-undo-check-in"),
        ("TK-UNUSED", "UNDO_CHECK_IN", "TICKET_NOT_CHECKED_IN", "req-batch-undo-check-in"),
    ]
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()
    assert "adminUserId" not in response.text
    assert "sql" not in response.text.lower()


def test_undo_check_in_reason_payload_rejects_blank_too_long_and_extra_fields():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    blank = client.post(
        "/api/admin/check-ins/TK-USED/undo",
        json={"reason": "   "},
        headers=headers,
    )
    too_long = client.post(
        "/api/admin/check-ins/TK-USED/undo",
        json={"reason": "误" * 101},
        headers=headers,
    )
    extra = client.post(
        "/api/admin/check-ins/TK-USED/undo",
        json={"reason": "误核销", "operatorUsername": "mallory"},
        headers=headers,
    )
    batch_blank = client.post(
        "/api/admin/check-ins/batch/undo",
        json={"ticketCodes": ["TK-USED"], "reason": "   "},
        headers=headers,
    )

    assert blank.status_code == 422
    assert too_long.status_code == 422
    assert extra.status_code == 422
    assert batch_blank.status_code == 422
    assert check_in_repo.undo_count == 0
    assert check_in_repo.audit_logs["TK-USED"] == []


def test_undo_check_in_reason_trims_before_length_validation():
    max_reason = "误" * 100

    single_auth_repo = FakeAuthRepository()
    single_check_in_repo = FakeCheckInRepository()
    single_client = build_client(single_auth_repo, single_check_in_repo)
    single_headers = login_admin(single_client, single_auth_repo)

    single = single_client.post(
        "/api/admin/check-ins/TK-USED/undo",
        json={"reason": f" {max_reason} "},
        headers=single_headers,
    )

    batch_auth_repo = FakeAuthRepository()
    batch_check_in_repo = FakeCheckInRepository()
    batch_client = build_client(batch_auth_repo, batch_check_in_repo)
    batch_headers = login_admin(batch_client, batch_auth_repo)

    batch = batch_client.post(
        "/api/admin/check-ins/batch/undo",
        json={"ticketCodes": ["TK-USED"], "reason": f" {max_reason} "},
        headers=batch_headers,
    )

    assert single.status_code == 200
    assert single_check_in_repo.audit_logs["TK-USED"][0].reason == max_reason
    assert batch.status_code == 200
    assert batch_check_in_repo.audit_logs["TK-USED"][0].reason == max_reason


def test_repeated_undo_check_in_returns_not_checked_without_extra_audit_log():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    first = client.post(
        "/api/admin/check-ins/TK-USED/undo",
        headers=headers | {"x-request-id": "req-undo-first"},
    )
    second = client.post(
        "/api/admin/check-ins/TK-USED/undo",
        headers=headers | {"x-request-id": "req-undo-second"},
    )
    logs = client.get("/api/admin/check-ins/TK-USED/logs")

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["code"] == "TICKET_NOT_CHECKED_IN"
    assert check_in_repo.undo_count == 1
    assert logs.status_code == 200
    assert len(logs.json()["data"]) == 1
    assert logs.json()["data"][0]["requestId"] == "req-undo-first"
    assert [
        (log.ticket_code, log.action, log.failure_code, log.request_id)
        for log in check_in_repo.failure_audit_logs
    ] == [("TK-USED", "UNDO_CHECK_IN", "TICKET_NOT_CHECKED_IN", "req-undo-second")]


def test_repeated_batch_undo_check_in_returns_not_checked_without_extra_audit_log():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    first = client.post(
        "/api/admin/check-ins/batch/undo",
        json={"ticketCodes": ["TK-USED"]},
        headers=headers | {"x-request-id": "req-batch-undo-first"},
    )
    second = client.post(
        "/api/admin/check-ins/batch/undo",
        json={"ticketCodes": ["TK-USED"]},
        headers=headers | {"x-request-id": "req-batch-undo-second"},
    )
    logs = client.get("/api/admin/check-ins/TK-USED/logs")

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["data"] == {
        "totalCount": 1,
        "successCount": 0,
        "failureCount": 1,
        "results": [
            {
                "ticketCode": "TK-USED",
                "success": False,
                "code": "TICKET_NOT_CHECKED_IN",
                "message": "票码未核销",
            }
        ],
    }
    assert check_in_repo.undo_count == 1
    assert logs.status_code == 200
    assert len(logs.json()["data"]) == 1
    assert logs.json()["data"][0]["requestId"] == "req-batch-undo-first"
    assert [
        (log.ticket_code, log.action, log.failure_code, log.request_id)
        for log in check_in_repo.failure_audit_logs
    ] == [("TK-USED", "UNDO_CHECK_IN", "TICKET_NOT_CHECKED_IN", "req-batch-undo-second")]


def test_batch_check_in_does_not_convert_system_app_errors_to_per_ticket_results():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    response = client.post(
        "/api/admin/check-ins/batch",
        json={"ticketCodes": ["TK-SYSTEM-ERROR", "TK-UNUSED"]},
        headers=headers,
    )

    assert response.status_code == 503
    assert response.json()["code"] == "CHECK_IN_UPSTREAM_UNAVAILABLE"
    assert "results" not in response.text
    assert check_in_repo.checked_in_count == 0
    assert check_in_repo.failure_audit_logs == []


def test_batch_undo_check_in_does_not_convert_system_app_errors_to_per_ticket_results():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    response = client.post(
        "/api/admin/check-ins/batch/undo",
        json={"ticketCodes": ["TK-SYSTEM-ERROR", "TK-USED"]},
        headers=headers,
    )

    assert response.status_code == 503
    assert response.json()["code"] == "CHECK_IN_UPSTREAM_UNAVAILABLE"
    assert "results" not in response.text
    assert check_in_repo.undo_count == 0
    assert check_in_repo.failure_audit_logs == []


def test_admin_can_read_check_in_audit_logs_after_success_without_csrf_header():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    check_in = client.post(
        "/api/admin/check-ins",
        json={"ticketCode": "TK-UNUSED"},
        headers=headers | {"x-request-id": "req-check-in-audit"},
    )
    logs = client.get("/api/admin/check-ins/TK-UNUSED/logs")

    assert check_in.status_code == 200
    assert logs.status_code == 200
    assert logs.json()["data"] == [
        {
            "orderNo": "O-PAID",
            "itemNo": "I-UNUSED",
            "ticketCode": "TK-UNUSED",
            "action": "CHECK_IN",
            "operatorUsername": "admin",
            "operatorDisplayName": "演示管理员",
            "requestId": "req-check-in-audit",
            "createdAt": "2026-07-01T10:30:00Z",
        }
    ]
    assert "adminUserId" not in logs.text
    assert "buyerPhone" not in logs.text
    assert "idNumber" not in logs.text
    assert "session" not in logs.text.lower()
    assert "csrf" not in logs.text.lower()


def test_check_in_audit_logs_require_admin_session_but_not_csrf_header():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)

    anonymous = client.get("/api/admin/check-ins/TK-UNUSED/logs")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/check-ins/TK-UNUSED/logs")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"

    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    login_admin(client, auth_repo)
    no_csrf = client.get("/api/admin/check-ins/TK-UNUSED/logs")
    missing = client.get("/api/admin/check-ins/TK-MISSING/logs")

    assert no_csrf.status_code == 200
    assert no_csrf.json()["data"] == []
    assert missing.status_code == 404
    assert missing.json()["code"] == "TICKET_NOT_FOUND"


def test_admin_can_search_check_in_failure_audit_logs_with_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    login_admin(client, auth_repo)
    check_in_repo.failure_audit_logs = [
        AdminCheckInFailureAuditLogRecord(
            ticket_code="TK-UNUSED",
            action="UNDO_CHECK_IN",
            failure_code="TICKET_NOT_CHECKED_IN",
            failure_message="票码未核销",
            operator_username="admin",
            operator_display_name="演示管理员",
            request_id="req-undo-unused",
            created_at=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
        ),
        AdminCheckInFailureAuditLogRecord(
            ticket_code="TK-MISSING",
            action="CHECK_IN",
            failure_code="TICKET_NOT_FOUND",
            failure_message="票码不存在",
            operator_username="admin",
            operator_display_name="演示管理员",
            request_id="req-missing",
            created_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        ),
        AdminCheckInFailureAuditLogRecord(
            ticket_code="TK-USED",
            action="CHECK_IN",
            failure_code="TICKET_ALREADY_USED",
            failure_message="票码已核销",
            operator_username="ops",
            operator_display_name="运营管理员",
            request_id="req-used",
            created_at=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        ),
    ]

    response = client.get(
        "/api/admin/check-in-failure-logs",
        params={
            "ticketCode": "unused",
            "failureCode": "ticket_not_checked_in",
            "operatorUsername": "adm",
            "dateFrom": "2026-07-01",
            "dateTo": "2026-07-31",
            "page": 1,
            "pageSize": 10,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "items": [
            {
                "ticketCode": "TK-UNUSED",
                "action": "UNDO_CHECK_IN",
                "failureCode": "TICKET_NOT_CHECKED_IN",
                "failureMessage": "票码未核销",
                "operatorUsername": "admin",
                "operatorDisplayName": "演示管理员",
                "requestId": "req-undo-unused",
                "createdAt": "2026-07-03T12:00:00Z",
            }
        ],
        "total": 1,
        "page": 1,
        "pageSize": 10,
    }
    assert check_in_repo.last_failure_audit_log_filters == AdminCheckInFailureAuditLogListFilter(
        ticket_code="unused",
        failure_code="TICKET_NOT_CHECKED_IN",
        operator_username="adm",
        date_from=date(2026, 7, 1),
        date_to=date(2026, 7, 31),
        page=1,
        page_size=10,
    )
    assert "adminUserId" not in response.text
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()
    assert "sql" not in response.text.lower()


def test_check_in_failure_audit_logs_require_admin_session_and_valid_filters():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)

    anonymous = client.get("/api/admin/check-in-failure-logs")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/check-in-failure-logs")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"
    assert check_in_repo.last_failure_audit_log_filters is None

    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    login_admin(client, auth_repo)

    invalid_code = client.get("/api/admin/check-in-failure-logs", params={"failureCode": "SQL_ERROR"})
    invalid_date_range = client.get(
        "/api/admin/check-in-failure-logs",
        params={"dateFrom": "2026-08-01", "dateTo": "2026-07-01"},
    )

    assert invalid_code.status_code == 422
    assert invalid_code.json()["code"] == "ADMIN_CHECK_IN_FAILURE_CODE_INVALID"
    assert invalid_date_range.status_code == 422
    assert invalid_date_range.json()["code"] == "ADMIN_CHECK_IN_FAILURE_LOG_DATE_RANGE_INVALID"
    assert check_in_repo.last_failure_audit_log_filters is None


def test_admin_can_export_check_in_failure_audit_logs_csv_with_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    login_admin(client, auth_repo)
    check_in_repo.failure_audit_logs = [
        AdminCheckInFailureAuditLogRecord(
            ticket_code="=TK-UNUSED",
            action="UNDO_CHECK_IN",
            failure_code="TICKET_NOT_CHECKED_IN",
            failure_message="+票码未核销",
            operator_username="@admin",
            operator_display_name=" 演示管理员",
            request_id="-req-undo-unused",
            created_at=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
        ),
        AdminCheckInFailureAuditLogRecord(
            ticket_code="TK-MISSING",
            action="CHECK_IN",
            failure_code="TICKET_NOT_FOUND",
            failure_message="票码不存在",
            operator_username="admin",
            operator_display_name="演示管理员",
            request_id="req-missing",
            created_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        ),
    ]

    response = client.get(
        "/api/admin/check-in-failure-logs.csv",
        params={
            "ticketCode": "unused",
            "failureCode": "ticket_not_checked_in",
            "operatorUsername": "adm",
            "dateFrom": "2026-07-03",
            "dateTo": "2026-07-03",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv; charset=utf-8")
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="admin-check-in-failure-logs-20260703-20260703.csv"'
    )
    assert response.content.startswith(b"\xef\xbb\xbf")
    assert check_in_repo.last_failure_audit_log_export_filters == AdminCheckInFailureAuditLogExportFilter(
        ticket_code="unused",
        failure_code="TICKET_NOT_CHECKED_IN",
        operator_username="adm",
        date_from=date(2026, 7, 3),
        date_to=date(2026, 7, 3),
        row_limit=EXPORT_FETCH_LIMIT,
    )
    assert csv_rows(response.text) == [
        {
            "ticketCode": "'=TK-UNUSED",
            "action": "UNDO_CHECK_IN",
            "failureCode": "TICKET_NOT_CHECKED_IN",
            "failureMessage": "'+票码未核销",
            "operatorUsername": "'@admin",
            "operatorDisplayName": " 演示管理员",
            "requestId": "'-req-undo-unused",
            "createdAt": "2026-07-03T12:00:00Z",
        }
    ]
    assert "adminUserId" not in response.text
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()
    assert "password" not in response.text.lower()
    assert "hash" not in response.text.lower()
    assert "sql" not in response.text.lower()


def test_check_in_failure_audit_log_csv_cells_escape_formula_like_prefixes_across_export_columns():
    csv_text = AdminCheckInService.to_check_in_failure_audit_logs_csv(
        [
            AdminCheckInFailureAuditLogRecord(
                ticket_code="=TICKET",
                action="CHECK_IN",
                failure_code="TICKET_NOT_FOUND",
                failure_message="+missing",
                operator_username="@admin",
                operator_display_name=" =display",
                request_id="\trequest",
                created_at=datetime(2026, 7, 3, 9, 0, tzinfo=UTC),
            )
        ]
    )

    assert csv_rows(csv_text) == [
        {
            "ticketCode": "'=TICKET",
            "action": "CHECK_IN",
            "failureCode": "TICKET_NOT_FOUND",
            "failureMessage": "'+missing",
            "operatorUsername": "'@admin",
            "operatorDisplayName": "' =display",
            "requestId": "'\trequest",
            "createdAt": "2026-07-03T09:00:00Z",
        }
    ]


def test_check_in_failure_audit_log_csv_export_requires_admin_session_and_valid_filters():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)

    anonymous = client.get("/api/admin/check-in-failure-logs.csv")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/check-in-failure-logs.csv")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"
    assert check_in_repo.last_failure_audit_log_export_filters is None

    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    login_admin(client, auth_repo)

    invalid_code = client.get("/api/admin/check-in-failure-logs.csv", params={"failureCode": "SQL_ERROR"})
    invalid_date_range = client.get(
        "/api/admin/check-in-failure-logs.csv",
        params={"dateFrom": "2026-08-01", "dateTo": "2026-07-01"},
    )
    no_csrf = client.get("/api/admin/check-in-failure-logs.csv")

    assert invalid_code.status_code == 422
    assert invalid_code.json()["code"] == "ADMIN_CHECK_IN_FAILURE_CODE_INVALID"
    assert invalid_date_range.status_code == 422
    assert invalid_date_range.json()["code"] == "ADMIN_CHECK_IN_FAILURE_LOG_DATE_RANGE_INVALID"
    assert no_csrf.status_code == 200
    assert csv_rows(no_csrf.text) == []
    assert check_in_repo.last_failure_audit_log_export_filters == AdminCheckInFailureAuditLogExportFilter(
        ticket_code=None,
        failure_code=None,
        operator_username=None,
        date_from=None,
        date_to=None,
        row_limit=EXPORT_FETCH_LIMIT,
    )


def test_admin_can_export_check_in_failure_audit_logs_xlsx_with_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    login_admin(client, auth_repo)
    check_in_repo.failure_audit_logs = [
        AdminCheckInFailureAuditLogRecord(
            ticket_code="=TK-UNUSED",
            action="UNDO_CHECK_IN",
            failure_code="TICKET_NOT_CHECKED_IN",
            failure_message="+票码未核销",
            operator_username="@admin",
            operator_display_name=" 演示管理员",
            request_id="-req-undo-unused",
            created_at=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
        ),
        AdminCheckInFailureAuditLogRecord(
            ticket_code="TK-MISSING",
            action="CHECK_IN",
            failure_code="TICKET_NOT_FOUND",
            failure_message="票码不存在",
            operator_username="other_admin",
            operator_display_name="其他管理员",
            request_id="req-missing",
            created_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        ),
    ]

    response = client.get(
        "/api/admin/check-in-failure-logs.xlsx",
        params={
            "ticketCode": "unused",
            "failureCode": "ticket_not_checked_in",
            "operatorUsername": "adm",
            "dateFrom": "2026-07-03",
            "dateTo": "2026-07-03",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="admin-check-in-failure-logs-20260703-20260703.xlsx"'
    )
    assert response.content.startswith(b"PK")
    assert check_in_repo.last_failure_audit_log_export_filters == AdminCheckInFailureAuditLogExportFilter(
        ticket_code="unused",
        failure_code="TICKET_NOT_CHECKED_IN",
        operator_username="adm",
        date_from=date(2026, 7, 3),
        date_to=date(2026, 7, 3),
        row_limit=EXPORT_FETCH_LIMIT,
    )
    assert xlsx_rows(response.content) == [
        [
            "ticketCode",
            "action",
            "failureCode",
            "failureMessage",
            "operatorUsername",
            "operatorDisplayName",
            "requestId",
            "createdAt",
        ],
        [
            "'=TK-UNUSED",
            "UNDO_CHECK_IN",
            "TICKET_NOT_CHECKED_IN",
            "'+票码未核销",
            "'@admin",
            " 演示管理员",
            "'-req-undo-unused",
            "2026-07-03T12:00:00Z",
        ],
    ]
    worksheet_text = xlsx_worksheet_text(response.content)
    assert "adminUserId" not in worksheet_text
    assert "buyerPhone" not in worksheet_text
    assert "idNumber" not in worksheet_text
    assert "session" not in worksheet_text.lower()
    assert "csrf" not in worksheet_text.lower()
    assert "password" not in worksheet_text.lower()
    assert "hash" not in worksheet_text.lower()
    assert "sql" not in worksheet_text.lower()


def test_check_in_failure_audit_log_xlsx_cells_escape_formula_like_prefixes():
    workbook = AdminCheckInService.to_check_in_failure_audit_logs_xlsx(
        [
            AdminCheckInFailureAuditLogRecord(
                ticket_code="=TICKET",
                action="CHECK_IN",
                failure_code="TICKET_NOT_FOUND",
                failure_message="+missing",
                operator_username="@admin",
                operator_display_name=" =display",
                request_id="\trequest",
                created_at=datetime(2026, 7, 3, 9, 0, tzinfo=UTC),
            )
        ]
    )

    assert xlsx_rows(workbook) == [
        [
            "ticketCode",
            "action",
            "failureCode",
            "failureMessage",
            "operatorUsername",
            "operatorDisplayName",
            "requestId",
            "createdAt",
        ],
        [
            "'=TICKET",
            "CHECK_IN",
            "TICKET_NOT_FOUND",
            "'+missing",
            "'@admin",
            "' =display",
            "'\trequest",
            "2026-07-03T09:00:00Z",
        ],
    ]


def test_check_in_failure_audit_log_xlsx_removes_xml_1_control_characters_from_text_cells():
    workbook = AdminCheckInService.to_check_in_failure_audit_logs_xlsx(
        [
            AdminCheckInFailureAuditLogRecord(
                ticket_code="TK-XML",
                action="CHECK_IN",
                failure_code="TICKET_NOT_FOUND",
                failure_message="bad\x0bmessage & <safe>",
                operator_username="demo_admin",
                operator_display_name="演示管理员",
                request_id="req-xml",
                created_at=datetime(2026, 7, 3, 9, 0, tzinfo=UTC),
            )
        ]
    )

    assert xlsx_rows(workbook)[1][3] == "badmessage & <safe>"
    worksheet_text = xlsx_worksheet_text(workbook)
    assert "\x0b" not in worksheet_text
    assert "badmessage &amp; &lt;safe&gt;" in worksheet_text


def test_check_in_failure_audit_log_xlsx_export_requires_admin_session_and_valid_filters():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)

    anonymous = client.get("/api/admin/check-in-failure-logs.xlsx")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/check-in-failure-logs.xlsx")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"
    assert check_in_repo.last_failure_audit_log_export_filters is None

    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    login_admin(client, auth_repo)

    invalid_code = client.get("/api/admin/check-in-failure-logs.xlsx", params={"failureCode": "SQL_ERROR"})
    invalid_date_range = client.get(
        "/api/admin/check-in-failure-logs.xlsx",
        params={"dateFrom": "2026-08-01", "dateTo": "2026-07-01"},
    )
    no_csrf = client.get("/api/admin/check-in-failure-logs.xlsx")

    assert invalid_code.status_code == 422
    assert invalid_code.json()["code"] == "ADMIN_CHECK_IN_FAILURE_CODE_INVALID"
    assert invalid_date_range.status_code == 422
    assert invalid_date_range.json()["code"] == "ADMIN_CHECK_IN_FAILURE_LOG_DATE_RANGE_INVALID"
    assert no_csrf.status_code == 200
    assert xlsx_rows(no_csrf.content) == [
        [
            "ticketCode",
            "action",
            "failureCode",
            "failureMessage",
            "operatorUsername",
            "operatorDisplayName",
            "requestId",
            "createdAt",
        ]
    ]
    assert check_in_repo.last_failure_audit_log_export_filters == AdminCheckInFailureAuditLogExportFilter(
        ticket_code=None,
        failure_code=None,
        operator_username=None,
        date_from=None,
        date_to=None,
        row_limit=EXPORT_FETCH_LIMIT,
    )


def test_admin_can_search_check_in_audit_logs_with_filters_and_pagination_without_csrf_header():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    login_admin(client, auth_repo)
    check_in_repo.audit_logs["TK-UNUSED"] = [
        AdminCheckInAuditLogRecord(
            order_no="O-PAID",
            item_no="I-UNUSED",
            ticket_code="TK-UNUSED",
            action="CHECK_IN",
            operator_username="admin",
            operator_display_name="演示管理员",
            request_id="req-check-in",
            created_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
            reason="现场误核销",
        ),
        AdminCheckInAuditLogRecord(
            order_no="O-OTHER",
            item_no="I-OTHER",
            ticket_code="TK-OTHER",
            action="CHECK_IN",
            operator_username="other_admin",
            operator_display_name="其他管理员",
            request_id="req-other",
            created_at=datetime(2026, 7, 1, 11, 30, tzinfo=UTC),
            reason="设备异常",
        ),
    ]

    response = client.get(
        "/api/admin/check-in-logs",
        params={
            "ticketCode": "unused",
            "orderNo": "paid",
            "operatorUsername": "adm",
            "reason": "误核",
            "dateFrom": "2026-07-02",
            "dateTo": "2026-07-02",
            "page": 1,
            "pageSize": 10,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "items": [
            {
                "orderNo": "O-PAID",
                "itemNo": "I-UNUSED",
                "ticketCode": "TK-UNUSED",
                "action": "CHECK_IN",
                "operatorUsername": "admin",
                "operatorDisplayName": "演示管理员",
                "requestId": "req-check-in",
                "reason": "现场误核销",
                "createdAt": "2026-07-02T12:00:00Z",
            }
        ],
        "total": 1,
        "page": 1,
        "pageSize": 10,
    }
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "adminUserId" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()


def test_check_in_audit_log_search_requires_admin_session_and_valid_filters():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)

    anonymous = client.get("/api/admin/check-in-logs")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/check-in-logs")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"

    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    login_admin(client, auth_repo)

    invalid_date_range = client.get(
        "/api/admin/check-in-logs",
        params={"dateFrom": "2026-07-03", "dateTo": "2026-07-01"},
    )
    no_csrf = client.get("/api/admin/check-in-logs")

    assert invalid_date_range.status_code == 422
    assert invalid_date_range.json()["code"] == "ADMIN_CHECK_IN_LOG_DATE_RANGE_INVALID"
    assert no_csrf.status_code == 200
    assert no_csrf.json()["data"] == {"items": [], "total": 0, "page": 1, "pageSize": 20}


def test_admin_can_export_check_in_audit_logs_csv_with_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    login_admin(client, auth_repo)
    check_in_repo.audit_logs["TK-UNUSED"] = [
        AdminCheckInAuditLogRecord(
            order_no="O-PAID",
            item_no="=I-UNUSED",
            ticket_code="TK-UNUSED",
            action="CHECK_IN",
            reason="=误核销",
            operator_username="+admin",
            operator_display_name=" 演示管理员",
            request_id="@req-check-in",
            created_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        ),
        AdminCheckInAuditLogRecord(
            order_no="O-OTHER",
            item_no="I-OTHER",
            ticket_code="TK-OTHER",
            action="CHECK_IN",
            operator_username="other_admin",
            operator_display_name="其他管理员",
            request_id="req-other",
            created_at=datetime(2026, 7, 1, 11, 30, tzinfo=UTC),
        ),
    ]

    response = client.get(
        "/api/admin/check-in-logs.csv",
        params={
            "ticketCode": "unused",
            "orderNo": "paid",
            "operatorUsername": "adm",
            "reason": "误核",
            "dateFrom": "2026-07-02",
            "dateTo": "2026-07-02",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv; charset=utf-8")
    assert response.headers["content-disposition"] == 'attachment; filename="admin-check-in-logs-20260702-20260702.csv"'
    assert response.content.startswith(b"\xef\xbb\xbf")
    assert check_in_repo.last_export_filters == AdminCheckInAuditLogExportFilter(
        ticket_code="unused",
        order_no="paid",
        operator_username="adm",
        reason="误核",
        date_from=date(2026, 7, 2),
        date_to=date(2026, 7, 2),
        row_limit=EXPORT_FETCH_LIMIT,
    )
    assert csv_rows(response.text) == [
        {
            "orderNo": "O-PAID",
            "itemNo": "'=I-UNUSED",
            "ticketCode": "TK-UNUSED",
            "action": "CHECK_IN",
            "reason": "'=误核销",
            "operatorUsername": "'+admin",
            "operatorDisplayName": " 演示管理员",
            "requestId": "'@req-check-in",
            "createdAt": "2026-07-02T12:00:00Z",
        }
    ]
    assert "adminUserId" not in response.text
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()
    assert "password" not in response.text.lower()
    assert "hash" not in response.text.lower()


def test_check_in_audit_log_export_rejects_rows_over_sync_export_limit(monkeypatch):
    monkeypatch.setattr(order_service_module, "SYNC_EXPORT_ROW_LIMIT", 1)
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    check_in_repo.audit_logs["TK-UNUSED"] = [
        AdminCheckInAuditLogRecord(
            order_no="O-PAID",
            item_no="I-UNUSED-1",
            ticket_code="TK-UNUSED",
            action="CHECK_IN",
            reason=None,
            operator_username="demo_admin",
            operator_display_name="演示管理员",
            request_id="req-1",
            created_at=datetime(2026, 7, 2, 10, 0, tzinfo=UTC),
        ),
        AdminCheckInAuditLogRecord(
            order_no="O-PAID",
            item_no="I-UNUSED-2",
            ticket_code="TK-UNUSED",
            action="UNDO_CHECK_IN",
            reason="误核销",
            operator_username="demo_admin",
            operator_display_name="演示管理员",
            request_id="req-2",
            created_at=datetime(2026, 7, 2, 11, 0, tzinfo=UTC),
        ),
    ]
    client = build_client(auth_repo, check_in_repo)
    login_admin(client, auth_repo)

    response = client.get("/api/admin/check-in-logs.csv")

    assert response.status_code == 413
    assert response.json()["code"] == "ADMIN_EXPORT_TOO_LARGE"
    assert check_in_repo.last_export_filters == AdminCheckInAuditLogExportFilter(
        ticket_code=None,
        order_no=None,
        operator_username=None,
        reason=None,
        date_from=None,
        date_to=None,
        row_limit=2,
    )


def test_check_in_audit_log_csv_cells_escape_formula_like_prefixes_across_export_columns():
    csv_text = AdminCheckInService.to_check_in_audit_logs_csv(
        [
            AdminCheckInAuditLogRecord(
                order_no="=ORDER",
                item_no="+ITEM",
                ticket_code="-TICKET",
                action="CHECK_IN",
                reason="+reason",
                operator_username="@admin",
                operator_display_name=" =display",
                request_id="\trequest",
                created_at=datetime(2026, 7, 3, 9, 0, tzinfo=UTC),
            )
        ]
    )

    assert csv_rows(csv_text) == [
        {
            "orderNo": "'=ORDER",
            "itemNo": "'+ITEM",
            "ticketCode": "'-TICKET",
            "action": "CHECK_IN",
            "reason": "'+reason",
            "operatorUsername": "'@admin",
            "operatorDisplayName": "' =display",
            "requestId": "'\trequest",
            "createdAt": "2026-07-03T09:00:00Z",
        }
    ]


def test_check_in_audit_log_csv_export_requires_admin_session_and_valid_filters():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)

    anonymous = client.get("/api/admin/check-in-logs.csv")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/check-in-logs.csv")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"

    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    login_admin(client, auth_repo)

    invalid_date_range = client.get(
        "/api/admin/check-in-logs.csv",
        params={"dateFrom": "2026-07-03", "dateTo": "2026-07-01"},
    )
    no_csrf = client.get("/api/admin/check-in-logs.csv")

    assert invalid_date_range.status_code == 422
    assert invalid_date_range.json()["code"] == "ADMIN_CHECK_IN_LOG_DATE_RANGE_INVALID"
    assert no_csrf.status_code == 200
    assert csv_rows(no_csrf.text) == []
    assert check_in_repo.last_export_filters == AdminCheckInAuditLogExportFilter(
        ticket_code=None,
        order_no=None,
        operator_username=None,
        reason=None,
        date_from=None,
        date_to=None,
        row_limit=EXPORT_FETCH_LIMIT,
    )


def test_admin_can_export_check_in_audit_logs_xlsx_with_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    login_admin(client, auth_repo)
    check_in_repo.audit_logs["TK-UNUSED"] = [
        AdminCheckInAuditLogRecord(
            order_no="O-PAID",
            item_no="=I-UNUSED",
            ticket_code="TK-UNUSED",
            action="CHECK_IN",
            reason="=误核销",
            operator_username="+admin",
            operator_display_name=" 演示管理员",
            request_id="@req-check-in",
            created_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        ),
        AdminCheckInAuditLogRecord(
            order_no="O-OTHER",
            item_no="I-OTHER",
            ticket_code="TK-OTHER",
            action="UNDO_CHECK_IN",
            operator_username="other_admin",
            operator_display_name="其他管理员",
            request_id="req-other",
            created_at=datetime(2026, 7, 1, 11, 30, tzinfo=UTC),
        ),
    ]

    response = client.get(
        "/api/admin/check-in-logs.xlsx",
        params={
            "ticketCode": "unused",
            "orderNo": "paid",
            "operatorUsername": "adm",
            "reason": "误核",
            "dateFrom": "2026-07-02",
            "dateTo": "2026-07-02",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert response.headers["content-disposition"] == 'attachment; filename="admin-check-in-logs-20260702-20260702.xlsx"'
    assert response.content.startswith(b"PK")
    assert check_in_repo.last_export_filters == AdminCheckInAuditLogExportFilter(
        ticket_code="unused",
        order_no="paid",
        operator_username="adm",
        reason="误核",
        date_from=date(2026, 7, 2),
        date_to=date(2026, 7, 2),
        row_limit=EXPORT_FETCH_LIMIT,
    )
    assert xlsx_rows(response.content) == [
        [
            "orderNo",
            "itemNo",
            "ticketCode",
            "action",
            "reason",
            "operatorUsername",
            "operatorDisplayName",
            "requestId",
            "createdAt",
        ],
        [
            "O-PAID",
            "'=I-UNUSED",
            "TK-UNUSED",
            "CHECK_IN",
            "'=误核销",
            "'+admin",
            " 演示管理员",
            "'@req-check-in",
            "2026-07-02T12:00:00Z",
        ],
    ]
    worksheet_text = xlsx_worksheet_text(response.content)
    assert "adminUserId" not in worksheet_text
    assert "buyerPhone" not in worksheet_text
    assert "idNumber" not in worksheet_text
    assert "session" not in worksheet_text.lower()
    assert "csrf" not in worksheet_text.lower()
    assert "password" not in worksheet_text.lower()
    assert "hash" not in worksheet_text.lower()


def test_check_in_audit_log_xlsx_removes_xml_1_control_characters_from_text_cells():
    workbook = AdminCheckInService.to_check_in_audit_logs_xlsx(
        [
            AdminCheckInAuditLogRecord(
                order_no="O-XML",
                item_no="I-XML",
                ticket_code="TK-XML",
                action="CHECK_IN",
                reason="bad\x0breason",
                operator_username="demo_admin",
                operator_display_name="bad\x0bname & <safe>",
                request_id="req-xml",
                created_at=datetime(2026, 7, 3, 9, 0, tzinfo=UTC),
            )
        ]
    )

    assert xlsx_rows(workbook)[1][4] == "badreason"
    assert xlsx_rows(workbook)[1][6] == "badname & <safe>"
    worksheet_text = xlsx_worksheet_text(workbook)
    assert "\x0b" not in worksheet_text
    assert "badreason" in worksheet_text
    assert "badname &amp; &lt;safe&gt;" in worksheet_text


def test_check_in_audit_log_xlsx_export_requires_admin_session_and_valid_filters():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)

    anonymous = client.get("/api/admin/check-in-logs.xlsx")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/check-in-logs.xlsx")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"

    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    login_admin(client, auth_repo)

    invalid_date_range = client.get(
        "/api/admin/check-in-logs.xlsx",
        params={"dateFrom": "2026-07-03", "dateTo": "2026-07-01"},
    )
    no_csrf = client.get("/api/admin/check-in-logs.xlsx")

    assert invalid_date_range.status_code == 422
    assert invalid_date_range.json()["code"] == "ADMIN_CHECK_IN_LOG_DATE_RANGE_INVALID"
    assert no_csrf.status_code == 200
    assert xlsx_rows(no_csrf.content) == [
        [
            "orderNo",
            "itemNo",
            "ticketCode",
            "action",
            "reason",
            "operatorUsername",
            "operatorDisplayName",
            "requestId",
            "createdAt",
        ]
    ]
    assert check_in_repo.last_export_filters == AdminCheckInAuditLogExportFilter(
        ticket_code=None,
        order_no=None,
        operator_username=None,
        reason=None,
        date_from=None,
        date_to=None,
        row_limit=EXPORT_FETCH_LIMIT,
    )


def test_failed_check_in_does_not_write_audit_log():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    response = client.post("/api/admin/check-ins", json={"ticketCode": "TK-USED"}, headers=headers)
    logs = client.get("/api/admin/check-ins/TK-USED/logs")

    assert response.status_code == 409
    assert response.json()["code"] == "TICKET_ALREADY_USED"
    assert logs.status_code == 200
    assert logs.json()["data"] == []


def test_admin_can_check_in_remaining_ticket_after_partial_refund():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    response = client.post("/api/admin/check-ins", json={"ticketCode": "TK-PARTIAL"}, headers=headers)

    assert response.status_code == 200
    assert response.json()["data"] == {
        "orderNo": "O-PARTIAL",
        "itemNo": "I-PARTIAL-UNUSED",
        "ticketCode": "TK-PARTIAL",
        "orderStatus": "COMPLETED",
        "itemStatus": "USED",
        "checkedInAt": "2026-07-01T10:30:00Z",
    }
    assert check_in_repo.checked_in_count == 1


def test_admin_check_in_requires_csrf_and_admin_session():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)

    anonymous = client.post("/api/admin/check-ins", json={"ticketCode": "TK-UNUSED"})
    assert anonymous.status_code == 403
    assert anonymous.json()["code"] == "CSRF_INVALID"

    anonymous_headers = csrf_headers(client)
    anonymous_with_csrf = client.post("/api/admin/check-ins", json={"ticketCode": "TK-UNUSED"}, headers=anonymous_headers)
    assert anonymous_with_csrf.status_code == 401
    assert anonymous_with_csrf.json()["code"] == "ADMIN_AUTH_REQUIRED"
    assert check_in_repo.failure_audit_logs == []

    visitor_headers = login_visitor(client)
    visitor = client.post("/api/admin/check-ins", json={"ticketCode": "TK-UNUSED"}, headers=visitor_headers)
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"
    assert check_in_repo.failure_audit_logs == []

    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    login_admin(client, auth_repo)
    missing_bound_csrf = client.post("/api/admin/check-ins", json={"ticketCode": "TK-UNUSED"})
    assert missing_bound_csrf.status_code == 403
    assert missing_bound_csrf.json()["code"] == "CSRF_INVALID"
    assert check_in_repo.checked_in_count == 0
    assert check_in_repo.failure_audit_logs == []


def test_admin_undo_check_in_requires_csrf_and_admin_session():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)

    anonymous = client.post("/api/admin/check-ins/TK-USED/undo")
    assert anonymous.status_code == 403
    assert anonymous.json()["code"] == "CSRF_INVALID"

    anonymous_headers = csrf_headers(client)
    anonymous_with_csrf = client.post("/api/admin/check-ins/TK-USED/undo", headers=anonymous_headers)
    assert anonymous_with_csrf.status_code == 401
    assert anonymous_with_csrf.json()["code"] == "ADMIN_AUTH_REQUIRED"

    visitor_headers = login_visitor(client)
    visitor = client.post("/api/admin/check-ins/TK-USED/undo", headers=visitor_headers)
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"

    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    login_admin(client, auth_repo)
    missing_bound_csrf = client.post("/api/admin/check-ins/TK-USED/undo")
    assert missing_bound_csrf.status_code == 403
    assert missing_bound_csrf.json()["code"] == "CSRF_INVALID"
    assert check_in_repo.undo_count == 0
    assert check_in_repo.failure_audit_logs == []


def test_admin_batch_check_in_requires_csrf_and_admin_session():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)

    anonymous = client.post("/api/admin/check-ins/batch", json={"ticketCodes": ["TK-UNUSED"]})
    assert anonymous.status_code == 403
    assert anonymous.json()["code"] == "CSRF_INVALID"

    anonymous_headers = csrf_headers(client)
    anonymous_with_csrf = client.post(
        "/api/admin/check-ins/batch",
        json={"ticketCodes": ["TK-UNUSED"]},
        headers=anonymous_headers,
    )
    assert anonymous_with_csrf.status_code == 401
    assert anonymous_with_csrf.json()["code"] == "ADMIN_AUTH_REQUIRED"

    visitor_headers = login_visitor(client)
    visitor = client.post(
        "/api/admin/check-ins/batch",
        json={"ticketCodes": ["TK-UNUSED"]},
        headers=visitor_headers,
    )
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"

    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    login_admin(client, auth_repo)
    missing_bound_csrf = client.post("/api/admin/check-ins/batch", json={"ticketCodes": ["TK-UNUSED"]})
    assert missing_bound_csrf.status_code == 403
    assert missing_bound_csrf.json()["code"] == "CSRF_INVALID"
    assert check_in_repo.checked_in_count == 0


def test_admin_batch_undo_check_in_requires_csrf_and_admin_session():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)

    anonymous = client.post("/api/admin/check-ins/batch/undo", json={"ticketCodes": ["TK-USED"]})
    assert anonymous.status_code == 403
    assert anonymous.json()["code"] == "CSRF_INVALID"

    anonymous_headers = csrf_headers(client)
    anonymous_with_csrf = client.post(
        "/api/admin/check-ins/batch/undo",
        json={"ticketCodes": ["TK-USED"]},
        headers=anonymous_headers,
    )
    assert anonymous_with_csrf.status_code == 401
    assert anonymous_with_csrf.json()["code"] == "ADMIN_AUTH_REQUIRED"

    visitor_headers = login_visitor(client)
    visitor = client.post(
        "/api/admin/check-ins/batch/undo",
        json={"ticketCodes": ["TK-USED"]},
        headers=visitor_headers,
    )
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"

    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    login_admin(client, auth_repo)
    missing_bound_csrf = client.post("/api/admin/check-ins/batch/undo", json={"ticketCodes": ["TK-USED"]})
    assert missing_bound_csrf.status_code == 403
    assert missing_bound_csrf.json()["code"] == "CSRF_INVALID"
    assert check_in_repo.undo_count == 0
    assert check_in_repo.failure_audit_logs == []


def test_batch_check_in_request_rejects_duplicate_empty_and_extra_fields():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    duplicate = client.post(
        "/api/admin/check-ins/batch",
        json={"ticketCodes": ["TK-UNUSED", " TK-UNUSED "]},
        headers=headers,
    )
    empty = client.post(
        "/api/admin/check-ins/batch",
        json={"ticketCodes": ["TK-UNUSED", "   "]},
        headers=headers,
    )
    extra = client.post(
        "/api/admin/check-ins/batch",
        json={"ticketCodes": ["TK-UNUSED"], "adminUserId": 1},
        headers=headers,
    )

    assert duplicate.status_code == 422
    assert duplicate.json()["code"] == "VALIDATION_ERROR"
    assert empty.status_code == 422
    assert empty.json()["code"] == "VALIDATION_ERROR"
    assert extra.status_code == 422
    assert extra.json()["code"] == "VALIDATION_ERROR"
    assert check_in_repo.checked_in_count == 0


def test_batch_undo_check_in_request_rejects_duplicate_empty_and_extra_fields():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    duplicate = client.post(
        "/api/admin/check-ins/batch/undo",
        json={"ticketCodes": ["TK-USED", " TK-USED "]},
        headers=headers,
    )
    empty = client.post(
        "/api/admin/check-ins/batch/undo",
        json={"ticketCodes": ["TK-USED", "   "]},
        headers=headers,
    )
    extra = client.post(
        "/api/admin/check-ins/batch/undo",
        json={"ticketCodes": ["TK-USED"], "adminUserId": 1},
        headers=headers,
    )
    too_long = client.post(
        "/api/admin/check-ins/batch/undo",
        json={"ticketCodes": ["T" * 65]},
        headers=headers,
    )

    assert duplicate.status_code == 422
    assert duplicate.json()["code"] == "VALIDATION_ERROR"
    assert empty.status_code == 422
    assert empty.json()["code"] == "VALIDATION_ERROR"
    assert extra.status_code == 422
    assert extra.json()["code"] == "VALIDATION_ERROR"
    assert too_long.status_code == 422
    assert too_long.json()["code"] == "VALIDATION_ERROR"
    assert check_in_repo.undo_count == 0


def test_repeated_check_in_returns_conflict_without_incrementing_checked_in_count():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    first = client.post("/api/admin/check-ins", json={"ticketCode": "TK-UNUSED"}, headers=headers)
    second = client.post("/api/admin/check-ins", json={"ticketCode": "TK-UNUSED"}, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["code"] == "TICKET_ALREADY_USED"
    assert check_in_repo.checked_in_count == 1


def test_check_in_missing_or_not_checkable_ticket_uses_domain_error_codes():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    missing = client.post("/api/admin/check-ins", json={"ticketCode": "TK-MISSING"}, headers=headers)
    used = client.post("/api/admin/check-ins", json={"ticketCode": "TK-USED"}, headers=headers)
    cancelled = client.post("/api/admin/check-ins", json={"ticketCode": "TK-CANCELLED"}, headers=headers)
    unpaid = client.post("/api/admin/check-ins", json={"ticketCode": "TK-UNPAID"}, headers=headers)
    refunded = client.post("/api/admin/check-ins", json={"ticketCode": "TK-REFUNDED"}, headers=headers)

    assert missing.status_code == 404
    assert missing.json()["code"] == "TICKET_NOT_FOUND"
    assert used.status_code == 409
    assert used.json()["code"] == "TICKET_ALREADY_USED"
    assert cancelled.status_code == 409
    assert cancelled.json()["code"] == "TICKET_NOT_CHECKABLE"
    assert unpaid.status_code == 409
    assert unpaid.json()["code"] == "TICKET_NOT_CHECKABLE"
    assert refunded.status_code == 409
    assert refunded.json()["code"] == "TICKET_NOT_CHECKABLE"
    assert check_in_repo.checked_in_count == 0


def test_undo_check_in_missing_not_checked_or_not_allowed_uses_domain_error_codes():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    missing = client.post("/api/admin/check-ins/TK-MISSING/undo", headers=headers)
    unused = client.post("/api/admin/check-ins/TK-UNUSED/undo", headers=headers)
    refunded = client.post("/api/admin/check-ins/TK-REFUNDED/undo", headers=headers)
    unpaid = client.post("/api/admin/check-ins/TK-USED-UNPAID/undo", headers=headers)
    cancelled = client.post("/api/admin/check-ins/TK-USED-CANCELLED/undo", headers=headers)

    assert missing.status_code == 404
    assert missing.json()["code"] == "TICKET_NOT_FOUND"
    assert unused.status_code == 409
    assert unused.json()["code"] == "TICKET_NOT_CHECKED_IN"
    assert refunded.status_code == 409
    assert refunded.json()["code"] == "TICKET_NOT_CHECKED_IN"
    assert unpaid.status_code == 409
    assert unpaid.json()["code"] == "TICKET_UNDO_NOT_ALLOWED"
    assert cancelled.status_code == 409
    assert cancelled.json()["code"] == "TICKET_UNDO_NOT_ALLOWED"
    assert check_in_repo.undo_count == 0
    assert [
        (log.ticket_code, log.action, log.failure_code, log.failure_message)
        for log in check_in_repo.failure_audit_logs
    ] == [
        ("TK-USED-CANCELLED", "UNDO_CHECK_IN", "TICKET_UNDO_NOT_ALLOWED", "当前票码不可撤销核销"),
        ("TK-USED-UNPAID", "UNDO_CHECK_IN", "TICKET_UNDO_NOT_ALLOWED", "当前票码不可撤销核销"),
        ("TK-REFUNDED", "UNDO_CHECK_IN", "TICKET_NOT_CHECKED_IN", "票码未核销"),
        ("TK-UNUSED", "UNDO_CHECK_IN", "TICKET_NOT_CHECKED_IN", "票码未核销"),
        ("TK-MISSING", "UNDO_CHECK_IN", "TICKET_NOT_FOUND", "票码不存在"),
    ]


def test_quota_checked_in_condition_failure_returns_not_checkable_without_incrementing_count():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    check_in_repo.quota_update_should_fail = True
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    response = client.post("/api/admin/check-ins", json={"ticketCode": "TK-UNUSED"}, headers=headers)

    assert response.status_code == 409
    assert response.json()["code"] == "TICKET_NOT_CHECKABLE"
    assert check_in_repo.checked_in_count == 0


def test_check_in_request_rejects_extra_client_control_fields():
    auth_repo = FakeAuthRepository()
    check_in_repo = FakeCheckInRepository()
    client = build_client(auth_repo, check_in_repo)
    headers = login_admin(client, auth_repo)

    response = client.post(
        "/api/admin/check-ins",
        json={
            "ticketCode": "TK-UNUSED",
            "adminUserId": 1,
            "itemStatus": "USED",
            "quotaCheckedIn": 100,
        },
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert "adminUserId" not in response.text
    assert check_in_repo.checked_in_count == 0


def test_postgres_check_in_locks_ticket_and_order_and_uses_parameterized_ticket_code(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "SELECT" in calls[-1][0] and "FROM ticket_order_item toi" in calls[-1][0]:
                return {
                    "order_item_id": 10,
                    "item_no": "I-UNUSED",
                    "ticket_code": "TK-UNUSED",
                    "item_status": "UNUSED",
                    "time_slot_id": 100,
                    "order_id": 1,
                    "order_no": "O-PAID",
                    "order_status": "PAID",
                    "payment_status": "PAID",
                }
            if "COUNT(*) AS remaining" in calls[-1][0]:
                return {"remaining": 0}
            if "UPDATE time_slot_quota" in calls[-1][0]:
                return {"id": 100}
            return None

    class FakeConnection:
        saw_exception = False

        def __enter__(self):
            return FakeCursor()

        def __exit__(self, exc_type, *_args):
            self.saw_exception = exc_type is not None
            return False

    connection = FakeConnection()
    monkeypatch.setattr(order_repository_module, "connect_db", lambda: connection)

    result = PostgresOrderRepository().check_in_ticket("TK-UNUSED", check_in_audit_input())

    assert result is not None
    assert result.order_status == "COMPLETED"
    assert result.item_status == "USED"
    assert result.raft_no == 1
    assert result.raft_seat_no == 1
    assert len(calls) == 7
    select_sql, select_params = calls[0]
    assert "FOR UPDATE OF toi, o" in select_sql
    assert "TK-UNUSED" not in select_sql
    assert select_params == ("TK-UNUSED",)
    assert "UPDATE time_slot_quota" in calls[1][0]
    assert "quota_checked_in + 1 <= quota_sold" in calls[1][0]
    assert "COUNT(*) AS assigned_count" in calls[2][0]
    assert "UPDATE ticket_order_item" in calls[3][0]
    assert "raft_no = %s" in calls[3][0]
    assert "item_status = 'UNUSED'" in calls[3][0]
    assert "UPDATE ticket_order" in calls[5][0]
    assert "INSERT INTO check_in_audit_log" in calls[6][0]
    assert calls[6][1][0:6] == (1, 10, "O-PAID", "I-UNUSED", "TK-UNUSED", "CHECK_IN")
    assert calls[6][1][6:] == (1, "demo_admin", "演示管理员", "req-test", None, result.checked_in_at)


def test_postgres_check_in_allows_remaining_ticket_after_partial_refund_and_ignores_refunded_items(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "SELECT" in calls[-1][0] and "FROM ticket_order_item toi" in calls[-1][0]:
                return {
                    "order_item_id": 10,
                    "item_no": "I-PARTIAL-UNUSED",
                    "ticket_code": "TK-PARTIAL",
                    "item_status": "UNUSED",
                    "time_slot_id": 100,
                    "order_id": 1,
                    "order_no": "O-PARTIAL",
                    "order_status": "PAID",
                    "payment_status": "PARTIAL_REFUND",
                }
            if "COUNT(*) AS remaining" in calls[-1][0]:
                return {"remaining": 0}
            if "UPDATE time_slot_quota" in calls[-1][0]:
                return {"id": 100}
            return None

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    result = PostgresOrderRepository().check_in_ticket("TK-PARTIAL", check_in_audit_input())

    assert result is not None
    assert result.order_status == "COMPLETED"
    assert result.item_status == "USED"
    assert result.raft_no == 1
    assert result.raft_seat_no == 1
    assert len(calls) == 7
    assert "item_status NOT IN ('USED', 'REFUNDED')" in calls[4][0]
    assert "UPDATE ticket_order" in calls[5][0]
    assert "INSERT INTO check_in_audit_log" in calls[6][0]


def test_postgres_undo_check_in_locks_ticket_decrements_quota_reverts_completed_order_and_audits(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "SELECT" in calls[-1][0] and "FROM ticket_order_item toi" in calls[-1][0]:
                return {
                    "order_item_id": 10,
                    "item_no": "I-USED",
                    "ticket_code": "TK-USED",
                    "item_status": "USED",
                    "time_slot_id": 100,
                    "order_id": 1,
                    "order_no": "O-PAID",
                    "order_status": "COMPLETED",
                    "payment_status": "PAID",
                }
            if "UPDATE ticket_order_item" in calls[-1][0]:
                return {"id": 10}
            if "UPDATE time_slot_quota" in calls[-1][0]:
                return {"id": 100}
            if "UPDATE ticket_order" in calls[-1][0]:
                return {"id": 1}
            return None

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    result = PostgresOrderRepository().undo_check_in_ticket("TK-USED", check_in_audit_input("现场误核销"))

    assert result is not None
    assert result.order_status == "PAID"
    assert result.item_status == "UNUSED"
    assert len(calls) == 5
    select_sql, select_params = calls[0]
    assert "FOR UPDATE OF toi, o" in select_sql
    assert "TK-USED" not in select_sql
    assert select_params == ("TK-USED",)
    assert "UPDATE ticket_order_item" in calls[1][0]
    assert "item_status = 'USED'" in calls[1][0]
    assert "UPDATE time_slot_quota" in calls[2][0]
    assert "quota_checked_in = quota_checked_in - 1" in calls[2][0]
    assert "quota_checked_in - 1 >= 0" in calls[2][0]
    assert "UPDATE ticket_order" in calls[3][0]
    assert "SET order_status = 'PAID'" in calls[3][0]
    assert "RETURNING id" in calls[3][0]
    assert "INSERT INTO check_in_audit_log" in calls[4][0]
    assert calls[4][1][0:6] == (1, 10, "O-PAID", "I-USED", "TK-USED", "UNDO_CHECK_IN")
    assert calls[4][1][6:] == (1, "demo_admin", "演示管理员", "req-test", "现场误核销", result.undone_at)


def test_postgres_undo_check_in_rejects_unchecked_ticket_before_updates(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            return {
                "order_item_id": 10,
                "item_no": "I-UNUSED",
                "ticket_code": "TK-UNUSED",
                "item_status": "UNUSED",
                "time_slot_id": 100,
                "order_id": 1,
                "order_no": "O-PAID",
                "order_status": "PAID",
                "payment_status": "PAID",
            }

    class FakeConnection:
        saw_exception = False

        def __enter__(self):
            return FakeCursor()

        def __exit__(self, exc_type, *_args):
            self.saw_exception = exc_type is not None
            return False

    connection = FakeConnection()
    monkeypatch.setattr(order_repository_module, "connect_db", lambda: connection)

    with pytest.raises(TicketNotCheckedInError):
        PostgresOrderRepository().undo_check_in_ticket("TK-UNUSED", check_in_audit_input())

    assert len(calls) == 1
    assert "FOR UPDATE OF toi, o" in calls[0][0]
    assert not any("UPDATE ticket_order_item" in sql for sql, _params in calls)
    assert not any("INSERT INTO check_in_audit_log" in sql for sql, _params in calls)


def test_postgres_undo_check_in_rejects_quota_decrement_failure_before_order_update_or_audit(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "SELECT" in calls[-1][0] and "FROM ticket_order_item toi" in calls[-1][0]:
                return {
                    "order_item_id": 10,
                    "item_no": "I-USED",
                    "ticket_code": "TK-USED",
                    "item_status": "USED",
                    "time_slot_id": 100,
                    "order_id": 1,
                    "order_no": "O-PAID",
                    "order_status": "COMPLETED",
                    "payment_status": "PAID",
                }
            if "UPDATE ticket_order_item" in calls[-1][0]:
                return {"id": 10}
            if "UPDATE time_slot_quota" in calls[-1][0]:
                return None
            return None

    class FakeConnection:
        saw_exception = False

        def __enter__(self):
            return FakeCursor()

        def __exit__(self, exc_type, *_args):
            self.saw_exception = exc_type is not None
            return False

    connection = FakeConnection()
    monkeypatch.setattr(order_repository_module, "connect_db", lambda: connection)

    with pytest.raises(TicketUndoNotAllowedError):
        PostgresOrderRepository().undo_check_in_ticket("TK-USED", check_in_audit_input())

    assert len(calls) == 3
    assert connection.saw_exception is True
    assert "UPDATE ticket_order_item" in calls[1][0]
    assert "UPDATE time_slot_quota" in calls[2][0]
    assert not any("UPDATE ticket_order\n" in sql for sql, _params in calls)
    assert not any("INSERT INTO check_in_audit_log" in sql for sql, _params in calls)


def test_postgres_undo_check_in_rejects_completed_order_update_failure_before_audit(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "SELECT" in calls[-1][0] and "FROM ticket_order_item toi" in calls[-1][0]:
                return {
                    "order_item_id": 10,
                    "item_no": "I-USED",
                    "ticket_code": "TK-USED",
                    "item_status": "USED",
                    "time_slot_id": 100,
                    "order_id": 1,
                    "order_no": "O-PAID",
                    "order_status": "COMPLETED",
                    "payment_status": "PAID",
                }
            if "UPDATE ticket_order_item" in calls[-1][0]:
                return {"id": 10}
            if "UPDATE time_slot_quota" in calls[-1][0]:
                return {"id": 100}
            if "UPDATE ticket_order" in calls[-1][0]:
                return None
            return None

    class FakeConnection:
        saw_exception = False

        def __enter__(self):
            return FakeCursor()

        def __exit__(self, exc_type, *_args):
            self.saw_exception = exc_type is not None
            return False

    connection = FakeConnection()
    monkeypatch.setattr(order_repository_module, "connect_db", lambda: connection)

    with pytest.raises(TicketUndoNotAllowedError):
        PostgresOrderRepository().undo_check_in_ticket("TK-USED", check_in_audit_input())

    assert len(calls) == 4
    assert connection.saw_exception is True
    assert "UPDATE ticket_order_item" in calls[1][0]
    assert "UPDATE time_slot_quota" in calls[2][0]
    assert "UPDATE ticket_order" in calls[3][0]
    assert "RETURNING id" in calls[3][0]
    assert not any("INSERT INTO check_in_audit_log" in sql for sql, _params in calls)


def test_postgres_check_in_audit_insert_failure_leaves_transaction_to_connection_rollback(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            if "INSERT INTO check_in_audit_log" in sql:
                raise RuntimeError("simulated audit insert failure")
            return self

        def fetchone(self):
            if "SELECT" in calls[-1][0] and "FROM ticket_order_item toi" in calls[-1][0]:
                return {
                    "order_item_id": 10,
                    "item_no": "I-UNUSED",
                    "ticket_code": "TK-UNUSED",
                    "item_status": "UNUSED",
                    "time_slot_id": 100,
                    "order_id": 1,
                    "order_no": "O-PAID",
                    "order_status": "PAID",
                    "payment_status": "PAID",
                }
            if "COUNT(*) AS remaining" in calls[-1][0]:
                return {"remaining": 0}
            if "UPDATE time_slot_quota" in calls[-1][0]:
                return {"id": 100}
            return None

    class FakeConnection:
        saw_exception = False

        def __enter__(self):
            return FakeCursor()

        def __exit__(self, exc_type, *_args):
            self.saw_exception = exc_type is not None
            return False

    connection = FakeConnection()
    monkeypatch.setattr(order_repository_module, "connect_db", lambda: connection)

    with pytest.raises(RuntimeError, match="simulated audit insert failure"):
        PostgresOrderRepository().check_in_ticket("TK-UNUSED", check_in_audit_input())

    queries = "\n".join(sql for sql, _params in calls)
    assert connection.saw_exception is True
    assert "UPDATE ticket_order_item" in queries
    assert "UPDATE time_slot_quota" in queries
    assert "UPDATE ticket_order" in queries
    assert "INSERT INTO check_in_audit_log" in queries


def test_postgres_list_check_in_audit_logs_reads_ticket_scoped_logs(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []
    created_at = datetime(2026, 7, 1, 10, 30, tzinfo=UTC)

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "SELECT id" in calls[-1][0] and "FROM ticket_order_item" in calls[-1][0]:
                return {"id": 10}
            return None

        def fetchall(self):
            return [
                {
                    "order_no": "O-PAID",
                    "item_no": "I-UNUSED",
                    "ticket_code": "TK-UNUSED",
                    "action": "CHECK_IN",
                    "reason": None,
                    "operator_username": "demo_admin",
                    "operator_display_name": "演示管理员",
                    "request_id": "req-test",
                    "created_at": created_at,
                }
            ]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    logs = PostgresOrderRepository().list_check_in_audit_logs("TK-UNUSED")

    assert len(logs) == 1
    assert logs[0].order_no == "O-PAID"
    assert logs[0].action == "CHECK_IN"
    assert logs[0].reason is None
    assert logs[0].operator_username == "demo_admin"
    assert calls[0][1] == ("TK-UNUSED",)
    assert "FROM ticket_order_item" in calls[0][0]
    assert "FROM check_in_audit_log" in calls[1][0]
    assert "ORDER BY created_at DESC, id DESC" in calls[1][0]
    assert "TK-UNUSED" not in calls[1][0]
    assert calls[1][1] == ("TK-UNUSED",)


def test_postgres_list_check_in_audit_logs_returns_none_for_missing_ticket(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            return None

        def fetchall(self):
            raise AssertionError("missing ticket must not query check_in_audit_log")

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    logs = PostgresOrderRepository().list_check_in_audit_logs("TK-MISSING")

    assert logs is None
    assert len(calls) == 1
    assert "FROM ticket_order_item" in calls[0][0]
    assert calls[0][1] == ("TK-MISSING",)


def test_postgres_list_check_in_audit_log_entries_filters_and_paginates(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []
    created_at = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "COUNT(*) AS total" in calls[-1][0]:
                return {"total": 1}
            return None

        def fetchall(self):
            return [
                {
                    "order_no": "O-PAID",
                    "item_no": "I-UNUSED",
                    "ticket_code": "TK-UNUSED",
                    "action": "CHECK_IN",
                    "reason": "现场误核销",
                    "operator_username": "demo_admin",
                    "operator_display_name": "演示管理员",
                    "request_id": "req-test",
                    "created_at": created_at,
                }
            ]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    result = PostgresOrderRepository().list_check_in_audit_log_entries(
        AdminCheckInAuditLogListFilter(
            ticket_code="unused",
            order_no="paid",
            operator_username="demo",
            reason="误核",
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 31),
            page=2,
            page_size=10,
        )
    )

    assert result.total == 1
    assert result.page == 2
    assert result.page_size == 10
    assert result.items[0].ticket_code == "TK-UNUSED"
    assert result.items[0].action == "CHECK_IN"
    assert result.items[0].reason == "现场误核销"
    assert "FROM check_in_audit_log cial" in calls[0][0]
    assert "UPPER(cial.ticket_code) LIKE UPPER(%s)" in calls[0][0]
    assert "UPPER(cial.order_no) LIKE UPPER(%s)" in calls[0][0]
    assert "UPPER(cial.operator_username) LIKE UPPER(%s)" in calls[0][0]
    assert "UPPER(cial.reason) LIKE UPPER(%s)" in calls[0][0]
    assert "cial.created_at::date >= %s" in calls[0][0]
    assert "cial.created_at::date <= %s" in calls[0][0]
    assert calls[0][1] == ("%unused%", "%paid%", "%demo%", "%误核%", date(2026, 7, 1), date(2026, 7, 31))
    assert "ORDER BY created_at DESC, id DESC" in calls[1][0]
    assert "LIMIT %s OFFSET %s" in calls[1][0]
    assert calls[1][1] == ("%unused%", "%paid%", "%demo%", "%误核%", date(2026, 7, 1), date(2026, 7, 31), 10, 10)


def test_postgres_check_in_audit_log_csv_export_uses_parameterized_filters(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []
    created_at = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchall(self):
            return [
                {
                    "order_no": "O-PAID",
                    "item_no": "I-UNUSED",
                    "ticket_code": "TK-UNUSED",
                    "action": "CHECK_IN",
                    "reason": "现场误核销",
                    "operator_username": "demo_admin",
                    "operator_display_name": "演示管理员",
                    "request_id": "req-test",
                    "created_at": created_at,
                }
            ]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    result = PostgresOrderRepository().list_check_in_audit_log_export_rows(
        AdminCheckInAuditLogExportFilter(
            ticket_code="unused",
            order_no="paid",
            operator_username="demo",
            reason="误核",
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 31),
        )
    )

    assert len(result) == 1
    assert result[0].ticket_code == "TK-UNUSED"
    assert result[0].action == "CHECK_IN"
    assert result[0].reason == "现场误核销"
    assert len(calls) == 1
    assert "FROM check_in_audit_log cial" in calls[0][0]
    assert "UPPER(cial.ticket_code) LIKE UPPER(%s)" in calls[0][0]
    assert "UPPER(cial.order_no) LIKE UPPER(%s)" in calls[0][0]
    assert "UPPER(cial.operator_username) LIKE UPPER(%s)" in calls[0][0]
    assert "UPPER(cial.reason) LIKE UPPER(%s)" in calls[0][0]
    assert "cial.created_at::date >= %s" in calls[0][0]
    assert "cial.created_at::date <= %s" in calls[0][0]
    assert "ORDER BY created_at DESC, id DESC" in calls[0][0]
    assert "LIMIT" not in calls[0][0]
    assert "2026-07-01" not in calls[0][0]
    assert "2026-07-31" not in calls[0][0]
    assert calls[0][1] == ("%unused%", "%paid%", "%demo%", "%误核%", date(2026, 7, 1), date(2026, 7, 31))


def test_postgres_list_check_in_audit_log_export_rows_applies_optional_row_limit(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchall(self):
            return []

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    PostgresOrderRepository().list_check_in_audit_log_export_rows(
        AdminCheckInAuditLogExportFilter(
            ticket_code="unused",
            order_no="paid",
            operator_username="demo",
            reason="误核",
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 31),
            row_limit=77,
        )
    )

    sql, params = calls[0]
    assert "FROM check_in_audit_log cial" in sql
    assert "LIMIT %s" in sql
    assert "77" not in sql
    assert params == ("%unused%", "%paid%", "%demo%", "%误核%", date(2026, 7, 1), date(2026, 7, 31), 77)


def test_postgres_check_in_failure_audit_export_rows_apply_optional_row_limit(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchall(self):
            return []

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    PostgresOrderRepository().list_check_in_failure_audit_log_export_rows(
        AdminCheckInFailureAuditLogExportFilter(
            ticket_code="missing",
            failure_code="TICKET_NOT_FOUND",
            operator_username="demo",
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 31),
            row_limit=77,
        )
    )

    sql, params = calls[0]
    assert "FROM check_in_failure_audit_log cifal" in sql
    assert "LIMIT %s" in sql
    assert "77" not in sql
    assert params == (
        "%missing%",
        "TICKET_NOT_FOUND",
        "%demo%",
        date(2026, 7, 1),
        date(2026, 7, 31),
        77,
    )


def test_postgres_records_check_in_failure_audit_log_with_parameterized_values(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    PostgresOrderRepository().record_check_in_failure_audit_log(
        ticket_code="TK-MISSING",
        action="UNDO_CHECK_IN",
        failure_code="TICKET_NOT_FOUND",
        failure_message="票码不存在",
        audit=check_in_audit_input(),
    )

    assert len(calls) == 1
    sql, params = calls[0]
    assert "INSERT INTO check_in_failure_audit_log" in sql
    assert "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)" in sql
    assert "TK-MISSING" not in sql
    assert "UNDO_CHECK_IN" not in sql
    assert "TICKET_NOT_FOUND" not in sql
    assert params[:8] == (
        "TK-MISSING",
        "UNDO_CHECK_IN",
        "TICKET_NOT_FOUND",
        "票码不存在",
        1,
        "demo_admin",
        "演示管理员",
        "req-test",
    )
    assert isinstance(params[8], datetime)


def test_postgres_list_check_in_failure_audit_log_entries_filters_and_paginates(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []
    created_at = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "COUNT(*) AS total" in calls[-1][0]:
                return {"total": 1}
            return None

        def fetchall(self):
            return [
                {
                    "ticket_code": "TK-MISSING",
                    "action": "CHECK_IN",
                    "failure_code": "TICKET_NOT_FOUND",
                    "failure_message": "票码不存在",
                    "operator_username": "demo_admin",
                    "operator_display_name": "演示管理员",
                    "request_id": "req-test",
                    "created_at": created_at,
                }
            ]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    result = PostgresOrderRepository().list_check_in_failure_audit_log_entries(
        AdminCheckInFailureAuditLogListFilter(
            ticket_code="missing",
            failure_code="TICKET_NOT_FOUND",
            operator_username="demo",
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 31),
            page=2,
            page_size=10,
        )
    )

    assert result.total == 1
    assert result.page == 2
    assert result.page_size == 10
    assert result.items[0].ticket_code == "TK-MISSING"
    assert result.items[0].failure_code == "TICKET_NOT_FOUND"
    assert "FROM check_in_failure_audit_log cifal" in calls[0][0]
    assert "UPPER(cifal.ticket_code) LIKE UPPER(%s)" in calls[0][0]
    assert "cifal.failure_code = %s" in calls[0][0]
    assert "UPPER(cifal.operator_username) LIKE UPPER(%s)" in calls[0][0]
    assert "cifal.created_at::date >= %s" in calls[0][0]
    assert "cifal.created_at::date <= %s" in calls[0][0]
    assert "TK-MISSING" not in calls[0][0]
    assert "TICKET_NOT_FOUND" not in calls[0][0]
    assert "2026-07-01" not in calls[0][0]
    assert "2026-07-31" not in calls[0][0]
    assert calls[0][1] == ("%missing%", "TICKET_NOT_FOUND", "%demo%", date(2026, 7, 1), date(2026, 7, 31))
    assert "ORDER BY created_at DESC, id DESC" in calls[1][0]
    assert "LIMIT %s OFFSET %s" in calls[1][0]
    assert calls[1][1] == (
        "%missing%",
        "TICKET_NOT_FOUND",
        "%demo%",
        date(2026, 7, 1),
        date(2026, 7, 31),
        10,
        10,
    )


def test_postgres_list_check_in_failure_audit_log_export_rows_uses_parameterized_filters(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []
    created_at = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchall(self):
            return [
                {
                    "ticket_code": "TK-MISSING",
                    "action": "CHECK_IN",
                    "failure_code": "TICKET_NOT_FOUND",
                    "failure_message": "票码不存在",
                    "operator_username": "demo_admin",
                    "operator_display_name": "演示管理员",
                    "request_id": "req-test",
                    "created_at": created_at,
                }
            ]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    result = PostgresOrderRepository().list_check_in_failure_audit_log_export_rows(
        AdminCheckInFailureAuditLogExportFilter(
            ticket_code="missing",
            failure_code="TICKET_NOT_FOUND",
            operator_username="demo",
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 31),
        )
    )

    assert result[0].ticket_code == "TK-MISSING"
    assert result[0].failure_code == "TICKET_NOT_FOUND"
    sql, params = calls[0]
    assert "FROM check_in_failure_audit_log cifal" in sql
    assert "UPPER(cifal.ticket_code) LIKE UPPER(%s)" in sql
    assert "cifal.failure_code = %s" in sql
    assert "UPPER(cifal.operator_username) LIKE UPPER(%s)" in sql
    assert "cifal.created_at::date >= %s" in sql
    assert "cifal.created_at::date <= %s" in sql
    assert "ORDER BY created_at DESC, id DESC" in sql
    assert "LIMIT %s OFFSET %s" not in sql
    assert "TK-MISSING" not in sql
    assert "TICKET_NOT_FOUND" not in sql
    assert "2026-07-01" not in sql
    assert "2026-07-31" not in sql
    assert params == ("%missing%", "TICKET_NOT_FOUND", "%demo%", date(2026, 7, 1), date(2026, 7, 31))


def test_postgres_check_in_rejects_unpaid_ticket_before_updates(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            return {
                "order_item_id": 10,
                "item_no": "I-UNPAID",
                "ticket_code": "TK-UNPAID",
                "item_status": "UNUSED",
                "time_slot_id": 100,
                "order_id": 1,
                "order_no": "O-UNPAID",
                "order_status": "PAID",
                "payment_status": "UNPAID",
            }

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    try:
        PostgresOrderRepository().check_in_ticket("TK-UNPAID", check_in_audit_input())
    except TicketNotCheckableError:
        pass
    else:
        raise AssertionError("unpaid ticket must not be checkable")

    assert len(calls) == 1
    assert "FOR UPDATE OF toi, o" in calls[0][0]
    assert not any("INSERT INTO check_in_audit_log" in sql for sql, _params in calls)


def test_postgres_check_in_rejects_quota_checked_in_condition_failure_before_order_update(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "SELECT" in calls[-1][0] and "FROM ticket_order_item toi" in calls[-1][0]:
                return {
                    "order_item_id": 10,
                    "item_no": "I-UNUSED",
                    "ticket_code": "TK-UNUSED",
                    "item_status": "UNUSED",
                    "time_slot_id": 100,
                    "order_id": 1,
                    "order_no": "O-PAID",
                    "order_status": "PAID",
                    "payment_status": "PAID",
                }
            if "UPDATE time_slot_quota" in calls[-1][0]:
                return None
            return None

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    try:
        PostgresOrderRepository().check_in_ticket("TK-UNUSED", check_in_audit_input())
    except TicketNotCheckableError:
        pass
    else:
        raise AssertionError("quota condition failure must not be checkable")

    assert len(calls) == 2
    assert "UPDATE time_slot_quota" in calls[1][0]
    assert not any("UPDATE ticket_order_item" in sql for sql, _params in calls)
    assert not any("COUNT(*) AS remaining" in sql for sql, _params in calls)
    assert not any("UPDATE ticket_order\n" in sql for sql, _params in calls)
    assert not any("INSERT INTO check_in_audit_log" in sql for sql, _params in calls)
