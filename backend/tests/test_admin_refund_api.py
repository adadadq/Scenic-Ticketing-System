import csv
import io
import zipfile
from datetime import UTC, date, datetime
from decimal import Decimal
from xml.etree import ElementTree

from fastapi.testclient import TestClient

import app.repositories.orders as order_repository_module
import app.services.orders as order_service_module
from app.main import create_app
from app.repositories.auth import get_auth_repository
from app.repositories.orders import (
    AdminPartialRefundRecord,
    AdminRefundAuditInput,
    AdminRefundAuditLogExportFilter,
    AdminRefundAuditLogRecord,
    AdminRefundAuditLogListFilter,
    AdminRefundAuditLogListRecord,
    AdminRefundRecord,
    OrderAlreadyRefundedError,
    OrderNotRefundableError,
    OrderRefundItemsInvalidError,
    PostgresOrderRepository,
    get_order_repository,
)
from app.services.orders import AdminRefundService, SYNC_EXPORT_ROW_LIMIT

from test_admin_auth_api import FakeAuthRepository, admin_login_payload, seed_enabled_admin
from test_auth_api import csrf_headers


EXPORT_FETCH_LIMIT = SYNC_EXPORT_ROW_LIMIT + 1


class FakeRefundRepository:
    def __init__(self):
        self.refund_count = 0
        self.partial_refund_count = 0
        self.orders = {
            "O-PAID": {
                "order_status": "PAID",
                "payment_status": "PAID",
                "item_nos": ["I-1", "I-2"],
                "item_statuses": ["UNUSED", "UNUSED"],
                "item_prices": [Decimal("128.00"), Decimal("128.00")],
                "paid_amount": Decimal("256.00"),
            },
            "O-REFUNDED": {
                "order_status": "REFUNDED",
                "payment_status": "REFUNDED",
                "item_nos": ["I-REFUNDED"],
                "item_statuses": ["REFUNDED"],
                "item_prices": [Decimal("128.00")],
                "paid_amount": Decimal("0.00"),
            },
            "O-UNPAID": {
                "order_status": "CREATED",
                "payment_status": "UNPAID",
                "item_nos": ["I-UNPAID"],
                "item_statuses": ["PENDING_PAYMENT"],
                "item_prices": [Decimal("128.00")],
                "paid_amount": Decimal("0.00"),
            },
            "O-USED": {
                "order_status": "PAID",
                "payment_status": "PAID",
                "item_nos": ["I-USED"],
                "item_statuses": ["USED"],
                "item_prices": [Decimal("128.00")],
                "paid_amount": Decimal("128.00"),
            },
        }
        self.quota_update_should_fail = False
        self.refund_logs: dict[str, list[AdminRefundAuditLogRecord]] = {order_no: [] for order_no in self.orders}
        self.last_export_filters: AdminRefundAuditLogExportFilter | None = None

    def refund_order(self, order_no: str, audit: AdminRefundAuditInput) -> AdminRefundRecord | None:
        order = self.orders.get(order_no)
        if order is None:
            return None
        if order["order_status"] == "REFUNDED" or order["payment_status"] == "REFUNDED":
            raise OrderAlreadyRefundedError
        if (
            self.quota_update_should_fail
            or order["order_status"] != "PAID"
            or order["payment_status"] != "PAID"
            or any(item_status != "UNUSED" for item_status in order["item_statuses"])
        ):
            raise OrderNotRefundableError

        self.refund_count += 1
        refunded_amount = order["paid_amount"]
        refunded_item_count = len(order["item_statuses"])
        order["order_status"] = "REFUNDED"
        order["payment_status"] = "REFUNDED"
        order["item_statuses"] = ["REFUNDED"] * refunded_item_count
        order["paid_amount"] = Decimal("0.00")
        self.refund_logs[order_no].insert(
            0,
            AdminRefundAuditLogRecord(
                order_no=order_no,
                refund_type="FULL",
                refunded_amount=refunded_amount,
                refunded_item_count=refunded_item_count,
                refunded_item_nos=list(order["item_nos"]),
                reason=audit.reason,
                operator_username=audit.operator_username,
                operator_display_name=audit.operator_display_name,
                request_id=audit.request_id,
                created_at=datetime(2026, 7, 1, 11, 30, tzinfo=UTC),
            ),
        )
        return AdminRefundRecord(
            order_no=order_no,
            order_status="REFUNDED",
            payment_status="REFUNDED",
            refunded_amount=refunded_amount,
            refunded_item_count=refunded_item_count,
            refunded_at=datetime(2026, 7, 1, 11, 30, tzinfo=UTC),
        )

    def refund_order_items(
        self,
        order_no: str,
        item_nos: list[str],
        audit: AdminRefundAuditInput,
    ) -> AdminPartialRefundRecord | None:
        order = self.orders.get(order_no)
        if order is None:
            return None
        if order["order_status"] == "REFUNDED" or order["payment_status"] == "REFUNDED":
            raise OrderAlreadyRefundedError
        if (
            self.quota_update_should_fail
            or order["order_status"] != "PAID"
            or order["payment_status"] not in ("PAID", "PARTIAL_REFUND")
            or any(item_status not in ("UNUSED", "REFUNDED") for item_status in order["item_statuses"])
        ):
            raise OrderNotRefundableError

        item_indexes = {item_no: index for index, item_no in enumerate(order["item_nos"])}
        if any(item_no not in item_indexes for item_no in item_nos):
            raise OrderRefundItemsInvalidError
        selected_indexes = [item_indexes[item_no] for item_no in item_nos]
        if any(order["item_statuses"][index] != "UNUSED" for index in selected_indexes):
            raise OrderNotRefundableError

        self.partial_refund_count += 1
        refunded_amount = sum((order["item_prices"][index] for index in selected_indexes), Decimal("0"))
        for index in selected_indexes:
            order["item_statuses"][index] = "REFUNDED"
        remaining_active = any(item_status != "REFUNDED" for item_status in order["item_statuses"])
        order["order_status"] = "PAID" if remaining_active else "REFUNDED"
        order["payment_status"] = "PARTIAL_REFUND" if remaining_active else "REFUNDED"
        order["paid_amount"] -= refunded_amount
        self.refund_logs[order_no].insert(
            0,
            AdminRefundAuditLogRecord(
                order_no=order_no,
                refund_type="PARTIAL",
                refunded_amount=refunded_amount,
                refunded_item_count=len(item_nos),
                refunded_item_nos=item_nos,
                reason=audit.reason,
                operator_username=audit.operator_username,
                operator_display_name=audit.operator_display_name,
                request_id=audit.request_id,
                created_at=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
            ),
        )
        return AdminPartialRefundRecord(
            order_no=order_no,
            order_status=order["order_status"],
            payment_status=order["payment_status"],
            refunded_amount=refunded_amount,
            refunded_item_count=len(item_nos),
            refunded_item_nos=item_nos,
            refunded_at=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        )

    def list_refund_audit_logs(self, order_no: str) -> list[AdminRefundAuditLogRecord] | None:
        if order_no not in self.orders:
            return None
        return self.refund_logs[order_no]

    def list_refund_audit_log_entries(
        self,
        filters: AdminRefundAuditLogListFilter,
    ) -> AdminRefundAuditLogListRecord:
        logs = [log for order_logs in self.refund_logs.values() for log in order_logs]
        if filters.refund_type:
            logs = [log for log in logs if log.refund_type == filters.refund_type]
        if filters.order_no:
            logs = [log for log in logs if filters.order_no.lower() in log.order_no.lower()]
        if filters.operator_username:
            logs = [log for log in logs if filters.operator_username.lower() in log.operator_username.lower()]
        if filters.date_from:
            logs = [log for log in logs if log.created_at.date() >= filters.date_from]
        if filters.date_to:
            logs = [log for log in logs if log.created_at.date() <= filters.date_to]
        logs = sorted(logs, key=lambda log: log.created_at, reverse=True)
        total = len(logs)
        start = (filters.page - 1) * filters.page_size
        end = start + filters.page_size
        return AdminRefundAuditLogListRecord(
            items=logs[start:end],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )

    def list_refund_audit_log_export_rows(
        self,
        filters: AdminRefundAuditLogExportFilter,
    ) -> list[AdminRefundAuditLogRecord]:
        self.last_export_filters = filters
        logs = [log for order_logs in self.refund_logs.values() for log in order_logs]
        if filters.refund_type:
            logs = [log for log in logs if log.refund_type == filters.refund_type]
        if filters.order_no:
            logs = [log for log in logs if filters.order_no.lower() in log.order_no.lower()]
        if filters.operator_username:
            logs = [log for log in logs if filters.operator_username.lower() in log.operator_username.lower()]
        if filters.date_from:
            logs = [log for log in logs if log.created_at.date() >= filters.date_from]
        if filters.date_to:
            logs = [log for log in logs if log.created_at.date() <= filters.date_to]
        return sorted(logs, key=lambda log: log.created_at, reverse=True)


def build_client(auth_repo: FakeAuthRepository, refund_repo: FakeRefundRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repo
    app.dependency_overrides[get_order_repository] = lambda: refund_repo
    return TestClient(app)


def login_admin(client: TestClient, auth_repo: FakeAuthRepository) -> dict[str, str]:
    seed_enabled_admin(auth_repo)
    headers = csrf_headers(client)
    response = client.post("/api/admin/auth/login", json=admin_login_payload(), headers=headers)
    assert response.status_code == 200
    return headers


def login_operator(client: TestClient, auth_repo: FakeAuthRepository) -> dict[str, str]:
    seed_enabled_admin(auth_repo, role="OPERATOR")
    headers = csrf_headers(client)
    response = client.post("/api/admin/auth/login", json=admin_login_payload(), headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["role"] == "OPERATOR"
    return headers


def login_visitor(client: TestClient) -> dict[str, str]:
    headers = csrf_headers(client)
    response = client.post("/api/auth/visitor/register", json={"username": "demo_visitor", "password": "Visitor123", "phone": "13911112222"}, headers=headers)
    assert response.status_code == 200
    return headers


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


def refund_audit_input(reason: str | None = "游客申请退款") -> AdminRefundAuditInput:
    return AdminRefundAuditInput(
        operator_admin_user_id=1,
        operator_username="demo_admin",
        operator_display_name="演示管理员",
        reason=reason,
        request_id="req-test",
    )


def test_admin_can_refund_paid_unused_order():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    headers = login_admin(client, auth_repo)

    response = client.post(
        "/api/admin/orders/O-PAID/refund",
        json={"reason": "游客申请退款"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "orderNo": "O-PAID",
        "orderStatus": "REFUNDED",
        "paymentStatus": "REFUNDED",
        "refundedAmount": "256.00",
        "refundedItemCount": 2,
        "refundedAt": "2026-07-01T11:30:00Z",
    }
    assert refund_repo.refund_count == 1
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()


def test_operator_cannot_refund_paid_order():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    headers = login_operator(client, auth_repo)

    response = client.post(
        "/api/admin/orders/O-PAID/refund",
        json={"reason": "游客申请退款"},
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["code"] == "ADMIN_FORBIDDEN"
    assert refund_repo.refund_count == 0
    assert refund_repo.orders["O-PAID"]["order_status"] == "PAID"
    assert refund_repo.refund_logs["O-PAID"] == []


def test_admin_can_read_refund_audit_logs_after_full_refund_without_csrf_header():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    headers = login_admin(client, auth_repo)

    refund_headers = headers | {"x-request-id": "req-full-refund-audit"}
    refund = client.post(
        "/api/admin/orders/O-PAID/refund",
        json={"reason": "游客申请退款"},
        headers=refund_headers,
    )
    logs = client.get("/api/admin/orders/O-PAID/refund-logs")

    assert refund.status_code == 200
    assert logs.status_code == 200
    assert logs.json()["data"] == [
        {
            "orderNo": "O-PAID",
            "refundType": "FULL",
            "refundedAmount": "256.00",
            "refundedItemCount": 2,
            "refundedItemNos": ["I-1", "I-2"],
            "reason": "游客申请退款",
            "operatorUsername": "admin",
            "operatorDisplayName": "演示管理员",
            "requestId": "req-full-refund-audit",
            "createdAt": "2026-07-01T11:30:00Z",
        }
    ]
    assert "adminUserId" not in logs.text
    assert "session" not in logs.text.lower()
    assert "csrf" not in logs.text.lower()


def test_refund_audit_log_bounds_request_id_and_keeps_nullable_fields():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    headers = login_admin(client, auth_repo)
    long_request_id = "r" * 80

    refund = client.post(
        "/api/admin/orders/O-PAID/refund",
        json={},
        headers=headers | {"x-request-id": long_request_id},
    )
    logs = client.get("/api/admin/orders/O-PAID/refund-logs")

    assert refund.status_code == 200
    assert refund.headers["x-request-id"] == long_request_id
    assert logs.status_code == 200
    assert logs.json()["data"][0]["reason"] is None
    assert logs.json()["data"][0]["requestId"] == long_request_id[:64]


def test_admin_can_partially_refund_selected_unused_items():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    headers = login_admin(client, auth_repo)

    response = client.post(
        "/api/admin/orders/O-PAID/refund/items",
        json={"itemNos": ["I-1"], "reason": "游客只退一张"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "orderNo": "O-PAID",
        "orderStatus": "PAID",
        "paymentStatus": "PARTIAL_REFUND",
        "refundedAmount": "128.00",
        "refundedItemCount": 1,
        "refundedItemNos": ["I-1"],
        "refundedAt": "2026-07-01T12:00:00Z",
    }
    assert refund_repo.partial_refund_count == 1
    assert refund_repo.orders["O-PAID"]["paid_amount"] == Decimal("128.00")
    assert refund_repo.orders["O-PAID"]["item_statuses"] == ["REFUNDED", "UNUSED"]
    assert "buyerPhone" not in response.text
    assert "idNumber" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()


def test_operator_cannot_partially_refund_selected_items():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    headers = login_operator(client, auth_repo)

    response = client.post(
        "/api/admin/orders/O-PAID/refund/items",
        json={"itemNos": ["I-1"], "reason": "游客只退一张"},
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["code"] == "ADMIN_FORBIDDEN"
    assert refund_repo.partial_refund_count == 0
    assert refund_repo.orders["O-PAID"]["paid_amount"] == Decimal("256.00")
    assert refund_repo.orders["O-PAID"]["item_statuses"] == ["UNUSED", "UNUSED"]
    assert refund_repo.refund_logs["O-PAID"] == []


def test_admin_can_read_refund_audit_logs_after_partial_refund_without_sensitive_fields():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    headers = login_admin(client, auth_repo)

    refund_headers = headers | {"x-request-id": "req-partial-refund-audit"}
    refund = client.post(
        "/api/admin/orders/O-PAID/refund/items",
        json={"itemNos": ["I-1"], "reason": "游客只退一张"},
        headers=refund_headers,
    )
    logs = client.get("/api/admin/orders/O-PAID/refund-logs")

    assert refund.status_code == 200
    assert logs.status_code == 200
    assert logs.json()["data"] == [
        {
            "orderNo": "O-PAID",
            "refundType": "PARTIAL",
            "refundedAmount": "128.00",
            "refundedItemCount": 1,
            "refundedItemNos": ["I-1"],
            "reason": "游客只退一张",
            "operatorUsername": "admin",
            "operatorDisplayName": "演示管理员",
            "requestId": "req-partial-refund-audit",
            "createdAt": "2026-07-01T12:00:00Z",
        }
    ]
    assert "buyerPhone" not in logs.text
    assert "idNumber" not in logs.text
    assert "adminUserId" not in logs.text


def test_admin_refund_requires_csrf_and_admin_session():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)

    anonymous = client.post("/api/admin/orders/O-PAID/refund", json={})
    assert anonymous.status_code == 403
    assert anonymous.json()["code"] == "CSRF_INVALID"

    anonymous_headers = csrf_headers(client)
    anonymous_with_csrf = client.post("/api/admin/orders/O-PAID/refund", json={}, headers=anonymous_headers)
    assert anonymous_with_csrf.status_code == 401
    assert anonymous_with_csrf.json()["code"] == "ADMIN_AUTH_REQUIRED"

    visitor_headers = login_visitor(client)
    visitor = client.post("/api/admin/orders/O-PAID/refund", json={}, headers=visitor_headers)
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"

    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    login_admin(client, auth_repo)
    missing_bound_csrf = client.post("/api/admin/orders/O-PAID/refund", json={})
    assert missing_bound_csrf.status_code == 403
    assert missing_bound_csrf.json()["code"] == "CSRF_INVALID"
    assert refund_repo.refund_count == 0


def test_admin_partial_refund_requires_csrf_and_admin_session():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)

    anonymous = client.post("/api/admin/orders/O-PAID/refund/items", json={"itemNos": ["I-1"]})
    assert anonymous.status_code == 403
    assert anonymous.json()["code"] == "CSRF_INVALID"

    anonymous_headers = csrf_headers(client)
    anonymous_with_csrf = client.post(
        "/api/admin/orders/O-PAID/refund/items",
        json={"itemNos": ["I-1"]},
        headers=anonymous_headers,
    )
    assert anonymous_with_csrf.status_code == 401
    assert anonymous_with_csrf.json()["code"] == "ADMIN_AUTH_REQUIRED"

    visitor_headers = login_visitor(client)
    visitor = client.post("/api/admin/orders/O-PAID/refund/items", json={"itemNos": ["I-1"]}, headers=visitor_headers)
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"

    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    login_admin(client, auth_repo)
    missing_bound_csrf = client.post("/api/admin/orders/O-PAID/refund/items", json={"itemNos": ["I-1"]})
    assert missing_bound_csrf.status_code == 403
    assert missing_bound_csrf.json()["code"] == "CSRF_INVALID"
    assert refund_repo.partial_refund_count == 0


def test_refund_audit_logs_require_admin_session_but_not_csrf_header():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)

    anonymous = client.get("/api/admin/orders/O-PAID/refund-logs")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    visitor_headers = login_visitor(client)
    visitor = client.get("/api/admin/orders/O-PAID/refund-logs", headers=visitor_headers)
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"

    admin_headers = login_admin(client, auth_repo)
    admin_without_csrf = client.get("/api/admin/orders/O-PAID/refund-logs")
    missing = client.get("/api/admin/orders/O-MISSING/refund-logs", headers=admin_headers)

    assert admin_without_csrf.status_code == 200
    assert admin_without_csrf.json()["data"] == []
    assert missing.status_code == 404
    assert missing.json()["code"] == "ADMIN_ORDER_NOT_FOUND"


def test_admin_can_search_refund_audit_logs_with_filters_and_pagination_without_csrf_header():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    login_admin(client, auth_repo)
    refund_repo.refund_logs["O-PAID"] = [
        AdminRefundAuditLogRecord(
            order_no="O-PAID",
            refund_type="PARTIAL",
            refunded_amount=Decimal("128.00"),
            refunded_item_count=1,
            refunded_item_nos=["I-1"],
            reason="游客只退一张",
            operator_username="admin",
            operator_display_name="演示管理员",
            request_id="req-partial",
            created_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        ),
        AdminRefundAuditLogRecord(
            order_no="O-PAID",
            refund_type="FULL",
            refunded_amount=Decimal("256.00"),
            refunded_item_count=2,
            refunded_item_nos=["I-1", "I-2"],
            reason="整单退款",
            operator_username="other_admin",
            operator_display_name="其他管理员",
            request_id="req-full",
            created_at=datetime(2026, 7, 1, 11, 30, tzinfo=UTC),
        ),
    ]

    response = client.get(
        "/api/admin/refund-logs",
        params={
            "refundType": "partial",
            "orderNo": "paid",
            "operatorUsername": "adm",
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
                "refundType": "PARTIAL",
                "refundedAmount": "128.00",
                "refundedItemCount": 1,
                "refundedItemNos": ["I-1"],
                "reason": "游客只退一张",
                "operatorUsername": "admin",
                "operatorDisplayName": "演示管理员",
                "requestId": "req-partial",
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


def test_refund_audit_log_search_requires_admin_session_and_valid_filters():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)

    anonymous = client.get("/api/admin/refund-logs")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/refund-logs")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"

    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    login_admin(client, auth_repo)

    invalid_type = client.get("/api/admin/refund-logs", params={"refundType": "chargeback"})
    invalid_date_range = client.get(
        "/api/admin/refund-logs",
        params={"dateFrom": "2026-07-03", "dateTo": "2026-07-01"},
    )
    no_csrf = client.get("/api/admin/refund-logs")

    assert invalid_type.status_code == 422
    assert invalid_type.json()["code"] == "ADMIN_REFUND_LOG_TYPE_INVALID"
    assert invalid_date_range.status_code == 422
    assert invalid_date_range.json()["code"] == "ADMIN_REFUND_LOG_DATE_RANGE_INVALID"
    assert no_csrf.status_code == 200
    assert no_csrf.json()["data"] == {"items": [], "total": 0, "page": 1, "pageSize": 20}


def test_admin_can_export_refund_audit_logs_csv_with_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    login_admin(client, auth_repo)
    refund_repo.refund_logs["O-PAID"] = [
        AdminRefundAuditLogRecord(
            order_no="O-PAID",
            refund_type="PARTIAL",
            refunded_amount=Decimal("128.00"),
            refunded_item_count=1,
            refunded_item_nos=["=ITEM", "I-1"],
            reason="=退款公式",
            operator_username="+admin",
            operator_display_name=" 演示管理员",
            request_id="@req-partial",
            created_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        ),
        AdminRefundAuditLogRecord(
            order_no="O-OTHER",
            refund_type="FULL",
            refunded_amount=Decimal("256.00"),
            refunded_item_count=2,
            refunded_item_nos=["I-2"],
            reason="不在筛选内",
            operator_username="other_admin",
            operator_display_name="其他管理员",
            request_id="req-full",
            created_at=datetime(2026, 7, 1, 11, 30, tzinfo=UTC),
        ),
    ]

    response = client.get(
        "/api/admin/refund-logs.csv",
        params={
            "refundType": "partial",
            "orderNo": "paid",
            "operatorUsername": "adm",
            "dateFrom": "2026-07-02",
            "dateTo": "2026-07-02",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv; charset=utf-8")
    assert response.headers["content-disposition"] == 'attachment; filename="admin-refund-logs-20260702-20260702.csv"'
    assert response.content.startswith(b"\xef\xbb\xbf")
    assert refund_repo.last_export_filters == AdminRefundAuditLogExportFilter(
        refund_type="PARTIAL",
        order_no="paid",
        operator_username="adm",
        date_from=date(2026, 7, 2),
        date_to=date(2026, 7, 2),
        row_limit=EXPORT_FETCH_LIMIT,
    )

    assert csv_rows(response.text) == [
        {
            "orderNo": "O-PAID",
            "refundType": "PARTIAL",
            "refundedAmount": "128.00",
            "refundedItemCount": "1",
            "refundedItemNos": "'=ITEM;I-1",
            "reason": "'=退款公式",
            "operatorUsername": "'+admin",
            "operatorDisplayName": " 演示管理员",
            "requestId": "'@req-partial",
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


def test_refund_audit_log_export_rejects_rows_over_sync_export_limit(monkeypatch):
    monkeypatch.setattr(order_service_module, "SYNC_EXPORT_ROW_LIMIT", 1)
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    refund_repo.refund_logs["O-PAID"] = [
        AdminRefundAuditLogRecord(
            order_no="O-PAID",
            refund_type="PARTIAL",
            refunded_amount=Decimal("128.00"),
            refunded_item_count=1,
            refunded_item_nos=["I-1"],
            reason="第一笔",
            operator_username="demo_admin",
            operator_display_name="演示管理员",
            request_id="req-1",
            created_at=datetime(2026, 7, 2, 10, 0, tzinfo=UTC),
        ),
        AdminRefundAuditLogRecord(
            order_no="O-PAID",
            refund_type="FULL",
            refunded_amount=Decimal("256.00"),
            refunded_item_count=2,
            refunded_item_nos=["I-1", "I-2"],
            reason="第二笔",
            operator_username="demo_admin",
            operator_display_name="演示管理员",
            request_id="req-2",
            created_at=datetime(2026, 7, 2, 11, 0, tzinfo=UTC),
        ),
    ]
    client = build_client(auth_repo, refund_repo)
    login_admin(client, auth_repo)

    response = client.get("/api/admin/refund-logs.csv")

    assert response.status_code == 413
    assert response.json()["code"] == "ADMIN_EXPORT_TOO_LARGE"
    assert refund_repo.last_export_filters == AdminRefundAuditLogExportFilter(
        refund_type=None,
        order_no=None,
        operator_username=None,
        date_from=None,
        date_to=None,
        row_limit=2,
    )


def test_refund_audit_log_csv_cells_escape_formula_like_prefixes_across_export_columns():
    csv_text = AdminRefundService.to_refund_audit_logs_csv(
        [
            AdminRefundAuditLogRecord(
                order_no="=ORDER",
                refund_type="FULL",
                refunded_amount=Decimal("128.00"),
                refunded_item_count=1,
                refunded_item_nos=["+ITEM"],
                reason="-reason",
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
            "refundType": "FULL",
            "refundedAmount": "128.00",
            "refundedItemCount": "1",
            "refundedItemNos": "'+ITEM",
            "reason": "'-reason",
            "operatorUsername": "'@admin",
            "operatorDisplayName": "' =display",
            "requestId": "'\trequest",
            "createdAt": "2026-07-03T09:00:00Z",
        }
    ]


def test_refund_audit_log_csv_export_requires_admin_session_and_valid_filters():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)

    anonymous = client.get("/api/admin/refund-logs.csv")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/refund-logs.csv")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"

    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    login_admin(client, auth_repo)

    invalid_type = client.get("/api/admin/refund-logs.csv", params={"refundType": "chargeback"})
    invalid_date_range = client.get(
        "/api/admin/refund-logs.csv",
        params={"dateFrom": "2026-07-03", "dateTo": "2026-07-01"},
    )
    no_csrf = client.get("/api/admin/refund-logs.csv")

    assert invalid_type.status_code == 422
    assert invalid_type.json()["code"] == "ADMIN_REFUND_LOG_TYPE_INVALID"
    assert invalid_date_range.status_code == 422
    assert invalid_date_range.json()["code"] == "ADMIN_REFUND_LOG_DATE_RANGE_INVALID"
    assert no_csrf.status_code == 200
    assert csv_rows(no_csrf.text) == []
    assert refund_repo.last_export_filters == AdminRefundAuditLogExportFilter(
        refund_type=None,
        order_no=None,
        operator_username=None,
        date_from=None,
        date_to=None,
        row_limit=EXPORT_FETCH_LIMIT,
    )


def test_admin_can_export_refund_audit_logs_xlsx_with_filters_without_csrf_header():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    login_admin(client, auth_repo)
    refund_repo.refund_logs["O-PAID"] = [
        AdminRefundAuditLogRecord(
            order_no="O-PAID",
            refund_type="PARTIAL",
            refunded_amount=Decimal("128.00"),
            refunded_item_count=1,
            refunded_item_nos=["=ITEM", "I-1"],
            reason="=退款公式",
            operator_username="+admin",
            operator_display_name=" 演示管理员",
            request_id="@req-partial",
            created_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        ),
        AdminRefundAuditLogRecord(
            order_no="O-OTHER",
            refund_type="FULL",
            refunded_amount=Decimal("256.00"),
            refunded_item_count=2,
            refunded_item_nos=["I-2"],
            reason="不在筛选内",
            operator_username="other_admin",
            operator_display_name="其他管理员",
            request_id="req-full",
            created_at=datetime(2026, 7, 1, 11, 30, tzinfo=UTC),
        ),
    ]

    response = client.get(
        "/api/admin/refund-logs.xlsx",
        params={
            "refundType": "partial",
            "orderNo": "paid",
            "operatorUsername": "adm",
            "dateFrom": "2026-07-02",
            "dateTo": "2026-07-02",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert response.headers["content-disposition"] == 'attachment; filename="admin-refund-logs-20260702-20260702.xlsx"'
    assert response.content.startswith(b"PK")
    assert refund_repo.last_export_filters == AdminRefundAuditLogExportFilter(
        refund_type="PARTIAL",
        order_no="paid",
        operator_username="adm",
        date_from=date(2026, 7, 2),
        date_to=date(2026, 7, 2),
        row_limit=EXPORT_FETCH_LIMIT,
    )
    assert xlsx_rows(response.content) == [
        [
            "orderNo",
            "refundType",
            "refundedAmount",
            "refundedItemCount",
            "refundedItemNos",
            "reason",
            "operatorUsername",
            "operatorDisplayName",
            "requestId",
            "createdAt",
        ],
        [
            "O-PAID",
            "PARTIAL",
            "128.00",
            "1",
            "'=ITEM;I-1",
            "'=退款公式",
            "'+admin",
            " 演示管理员",
            "'@req-partial",
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


def test_refund_audit_log_xlsx_removes_xml_1_control_characters_from_text_cells():
    workbook = AdminRefundService.to_refund_audit_logs_xlsx(
        [
            AdminRefundAuditLogRecord(
                order_no="O-XML",
                refund_type="FULL",
                refunded_amount=Decimal("128.00"),
                refunded_item_count=1,
                refunded_item_nos=["I-XML"],
                reason="bad\x0breason & <safe>",
                operator_username="demo_admin",
                operator_display_name="演示管理员",
                request_id="req-xml",
                created_at=datetime(2026, 7, 3, 9, 0, tzinfo=UTC),
            )
        ]
    )

    assert xlsx_rows(workbook)[1][5] == "badreason & <safe>"
    worksheet_text = xlsx_worksheet_text(workbook)
    assert "\x0b" not in worksheet_text
    assert "badreason &amp; &lt;safe&gt;" in worksheet_text


def test_refund_audit_log_xlsx_escapes_formula_prefix_after_xml_control_character_cleanup():
    workbook = AdminRefundService.to_refund_audit_logs_xlsx(
        [
            AdminRefundAuditLogRecord(
                order_no="O-FORMULA",
                refund_type="FULL",
                refunded_amount=Decimal("128.00"),
                refunded_item_count=1,
                refunded_item_nos=["I-FORMULA"],
                reason="\x0b=1+1",
                operator_username="demo_admin",
                operator_display_name="演示管理员",
                request_id="req-formula",
                created_at=datetime(2026, 7, 3, 9, 0, tzinfo=UTC),
            )
        ]
    )

    assert xlsx_rows(workbook)[1][5] == "'=1+1"
    assert "<f>" not in xlsx_worksheet_text(workbook)


def test_refund_audit_log_xlsx_export_requires_admin_session_and_valid_filters():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)

    anonymous = client.get("/api/admin/refund-logs.xlsx")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor = client.get("/api/admin/refund-logs.xlsx")
    assert visitor.status_code == 403
    assert visitor.json()["code"] == "ADMIN_FORBIDDEN"

    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    login_admin(client, auth_repo)

    invalid_type = client.get("/api/admin/refund-logs.xlsx", params={"refundType": "chargeback"})
    invalid_date_range = client.get(
        "/api/admin/refund-logs.xlsx",
        params={"dateFrom": "2026-07-03", "dateTo": "2026-07-01"},
    )
    no_csrf = client.get("/api/admin/refund-logs.xlsx")

    assert invalid_type.status_code == 422
    assert invalid_type.json()["code"] == "ADMIN_REFUND_LOG_TYPE_INVALID"
    assert invalid_date_range.status_code == 422
    assert invalid_date_range.json()["code"] == "ADMIN_REFUND_LOG_DATE_RANGE_INVALID"
    assert no_csrf.status_code == 200
    assert xlsx_rows(no_csrf.content) == [
        [
            "orderNo",
            "refundType",
            "refundedAmount",
            "refundedItemCount",
            "refundedItemNos",
            "reason",
            "operatorUsername",
            "operatorDisplayName",
            "requestId",
            "createdAt",
        ]
    ]
    assert refund_repo.last_export_filters == AdminRefundAuditLogExportFilter(
        refund_type=None,
        order_no=None,
        operator_username=None,
        date_from=None,
        date_to=None,
        row_limit=EXPORT_FETCH_LIMIT,
    )


def test_refund_missing_already_refunded_or_not_refundable_order_uses_domain_error_codes():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    headers = login_admin(client, auth_repo)

    missing = client.post("/api/admin/orders/O-MISSING/refund", json={}, headers=headers)
    refunded = client.post("/api/admin/orders/O-REFUNDED/refund", json={}, headers=headers)
    unpaid = client.post("/api/admin/orders/O-UNPAID/refund", json={}, headers=headers)
    used = client.post("/api/admin/orders/O-USED/refund", json={}, headers=headers)

    assert missing.status_code == 404
    assert missing.json()["code"] == "ADMIN_ORDER_NOT_FOUND"
    assert refunded.status_code == 409
    assert refunded.json()["code"] == "ORDER_ALREADY_REFUNDED"
    assert unpaid.status_code == 409
    assert unpaid.json()["code"] == "ORDER_NOT_REFUNDABLE"
    assert used.status_code == 409
    assert used.json()["code"] == "ORDER_NOT_REFUNDABLE"
    assert refund_repo.refund_count == 0


def test_partial_refund_missing_invalid_or_not_refundable_order_uses_domain_error_codes():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    headers = login_admin(client, auth_repo)

    missing = client.post("/api/admin/orders/O-MISSING/refund/items", json={"itemNos": ["I-1"]}, headers=headers)
    invalid_item = client.post("/api/admin/orders/O-PAID/refund/items", json={"itemNos": ["I-MISSING"]}, headers=headers)
    refunded = client.post(
        "/api/admin/orders/O-REFUNDED/refund/items",
        json={"itemNos": ["I-REFUNDED"]},
        headers=headers,
    )
    unpaid = client.post("/api/admin/orders/O-UNPAID/refund/items", json={"itemNos": ["I-UNPAID"]}, headers=headers)
    used = client.post("/api/admin/orders/O-USED/refund/items", json={"itemNos": ["I-USED"]}, headers=headers)

    assert missing.status_code == 404
    assert missing.json()["code"] == "ADMIN_ORDER_NOT_FOUND"
    assert invalid_item.status_code == 409
    assert invalid_item.json()["code"] == "ORDER_REFUND_ITEMS_INVALID"
    assert refunded.status_code == 409
    assert refunded.json()["code"] == "ORDER_ALREADY_REFUNDED"
    assert unpaid.status_code == 409
    assert unpaid.json()["code"] == "ORDER_NOT_PARTIALLY_REFUNDABLE"
    assert used.status_code == 409
    assert used.json()["code"] == "ORDER_NOT_PARTIALLY_REFUNDABLE"
    assert refund_repo.partial_refund_count == 0


def test_repeated_refund_does_not_restock_twice():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    headers = login_admin(client, auth_repo)

    first = client.post("/api/admin/orders/O-PAID/refund", json={}, headers=headers)
    second = client.post("/api/admin/orders/O-PAID/refund", json={}, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["code"] == "ORDER_ALREADY_REFUNDED"
    assert refund_repo.refund_count == 1


def test_partial_refund_request_rejects_extra_client_control_fields_and_duplicate_items():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    headers = login_admin(client, auth_repo)

    extra = client.post(
        "/api/admin/orders/O-PAID/refund/items",
        json={
            "itemNos": ["I-1"],
            "reason": "游客只退一张",
            "refundAmount": "0.01",
            "orderStatus": "REFUNDED",
            "paymentStatus": "REFUNDED",
            "quotaSold": 0,
        },
        headers=headers,
    )
    duplicate = client.post(
        "/api/admin/orders/O-PAID/refund/items",
        json={"itemNos": ["I-1", "I-1"]},
        headers=headers,
    )

    assert extra.status_code == 422
    assert extra.json()["code"] == "VALIDATION_ERROR"
    assert duplicate.status_code == 422
    assert duplicate.json()["code"] == "VALIDATION_ERROR"
    assert "refundAmount" not in extra.text
    assert refund_repo.partial_refund_count == 0


def test_refund_request_rejects_extra_client_control_fields():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    client = build_client(auth_repo, refund_repo)
    headers = login_admin(client, auth_repo)

    response = client.post(
        "/api/admin/orders/O-PAID/refund",
        json={
            "reason": "游客申请退款",
            "adminUserId": 1,
            "orderStatus": "REFUNDED",
            "paidAmount": 0,
            "quotaSold": 0,
        },
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert "adminUserId" not in response.text
    assert refund_repo.refund_count == 0


def test_quota_restock_condition_failure_returns_not_refundable_without_restocking_twice():
    auth_repo = FakeAuthRepository()
    refund_repo = FakeRefundRepository()
    refund_repo.quota_update_should_fail = True
    client = build_client(auth_repo, refund_repo)
    headers = login_admin(client, auth_repo)

    response = client.post("/api/admin/orders/O-PAID/refund", json={}, headers=headers)

    assert response.status_code == 409
    assert response.json()["code"] == "ORDER_NOT_REFUNDABLE"
    assert refund_repo.refund_count == 0


def test_postgres_refund_locks_order_and_items_and_restock_slots(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "SELECT" in calls[-1][0] and "FROM ticket_order\n" in calls[-1][0]:
                return {
                    "order_id": 1,
                    "order_no": "O-PAID",
                    "order_status": "PAID",
                    "payment_status": "PAID",
                    "paid_amount": Decimal("256.00"),
                }
            if "SELECT" in calls[-1][0] and "FROM payment_record\n" in calls[-1][0]:
                return {"payment_record_id": 200}
            if "UPDATE time_slot_quota" in calls[-1][0]:
                return {"id": 100}
            if "UPDATE payment_record" in calls[-1][0]:
                return {"id": 200}
            return None

        def fetchall(self):
            return [
                {
                    "order_item_id": 10,
                    "item_no": "I-1",
                    "item_status": "UNUSED",
                    "time_slot_id": 100,
                    "final_price": Decimal("128.00"),
                },
                {
                    "order_item_id": 11,
                    "item_no": "I-2",
                    "item_status": "UNUSED",
                    "time_slot_id": 100,
                    "final_price": Decimal("128.00"),
                },
            ]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    result = PostgresOrderRepository().refund_order("O-PAID", refund_audit_input())

    assert result is not None
    assert result.order_status == "REFUNDED"
    assert result.payment_status == "REFUNDED"
    assert result.refunded_amount == Decimal("256.00")
    assert result.refunded_item_count == 2
    assert len(calls) == 8
    assert "FOR UPDATE" in calls[0][0]
    assert calls[0][1] == ("O-PAID",)
    assert "FOR UPDATE" in calls[1][0]
    assert "FROM payment_record" in calls[2][0]
    assert "FOR UPDATE" in calls[2][0]
    assert "UPDATE time_slot_quota" in calls[3][0]
    assert "quota_sold - %s >= quota_checked_in" in calls[3][0]
    assert "UPDATE ticket_order_item" in calls[4][0]
    assert "UPDATE payment_record" in calls[5][0]
    assert "RETURNING id" in calls[5][0]
    assert "UPDATE ticket_order" in calls[6][0]
    assert "INSERT INTO refund_audit_log" in calls[7][0]
    assert calls[7][1][2:6] == ("FULL", Decimal("256.00"), 2, '["I-1", "I-2"]')


def test_postgres_partial_refund_locks_order_items_and_updates_selected_ticket_only(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "SELECT" in calls[-1][0] and "FROM ticket_order\n" in calls[-1][0]:
                return {
                    "order_id": 1,
                    "order_no": "O-PAID",
                    "order_status": "PAID",
                    "payment_status": "PAID",
                    "paid_amount": Decimal("256.00"),
                }
            if "SELECT" in calls[-1][0] and "FROM payment_record\n" in calls[-1][0]:
                return {"payment_record_id": 200}
            if "UPDATE time_slot_quota" in calls[-1][0]:
                return {"id": 100}
            if "UPDATE ticket_order\n" in calls[-1][0]:
                return {"id": 1}
            return None

        def fetchall(self):
            if "UPDATE ticket_order_item" in calls[-1][0]:
                return [{"item_no": "I-1"}]
            return [
                {
                    "order_item_id": 10,
                    "item_no": "I-1",
                    "item_status": "UNUSED",
                    "time_slot_id": 100,
                    "final_price": Decimal("128.00"),
                },
                {
                    "order_item_id": 11,
                    "item_no": "I-2",
                    "item_status": "UNUSED",
                    "time_slot_id": 100,
                    "final_price": Decimal("128.00"),
                },
            ]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    result = PostgresOrderRepository().refund_order_items("O-PAID", ["I-1"], refund_audit_input())

    assert result is not None
    assert result.order_status == "PAID"
    assert result.payment_status == "PARTIAL_REFUND"
    assert result.refunded_amount == Decimal("128.00")
    assert result.refunded_item_count == 1
    assert result.refunded_item_nos == ["I-1"]
    assert len(calls) == 7
    assert "FOR UPDATE" in calls[0][0]
    assert calls[0][1] == ("O-PAID",)
    assert "FOR UPDATE" in calls[1][0]
    assert "FROM payment_record" in calls[2][0]
    assert "FOR UPDATE" in calls[2][0]
    assert "UPDATE time_slot_quota" in calls[3][0]
    assert "quota_sold - %s >= quota_checked_in" in calls[3][0]
    assert "UPDATE ticket_order_item" in calls[4][0]
    assert "I-1" not in calls[4][0]
    assert calls[4][1][-1] == "I-1"
    assert "RETURNING item_no" in calls[4][0]
    assert "UPDATE ticket_order" in calls[5][0]
    assert calls[5][1][0:3] == ("PAID", "PARTIAL_REFUND", Decimal("128.00"))
    assert "INSERT INTO refund_audit_log" in calls[6][0]
    assert calls[6][1][2:6] == ("PARTIAL", Decimal("128.00"), 1, '["I-1"]')
    assert not any("UPDATE payment_record" in sql for sql, _params in calls)


def test_postgres_list_refund_audit_logs_reads_order_scoped_logs(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []
    created_at = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "SELECT id AS order_id" in calls[-1][0]:
                return {"order_id": 1}
            return None

        def fetchall(self):
            return [
                {
                    "order_no": "O-PAID",
                    "refund_type": "PARTIAL",
                    "refunded_amount": Decimal("128.00"),
                    "refunded_item_count": 1,
                    "refunded_item_nos": '["I-1"]',
                    "reason": "游客申请退款",
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

    logs = PostgresOrderRepository().list_refund_audit_logs("O-PAID")

    assert len(logs) == 1
    assert logs[0].order_no == "O-PAID"
    assert logs[0].refund_type == "PARTIAL"
    assert logs[0].refunded_item_nos == ["I-1"]
    assert logs[0].operator_username == "demo_admin"
    assert calls[0][1] == ("O-PAID",)
    assert "FROM ticket_order" in calls[0][0]
    assert "FROM refund_audit_log" in calls[1][0]
    assert "ORDER BY created_at DESC, id DESC" in calls[1][0]
    assert calls[1][1] == (1,)


def test_postgres_list_refund_audit_logs_returns_none_for_missing_order(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            return None

        def fetchall(self):
            raise AssertionError("missing order must not query refund_audit_log")

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    logs = PostgresOrderRepository().list_refund_audit_logs("O-MISSING")

    assert logs is None
    assert len(calls) == 1
    assert "FROM ticket_order" in calls[0][0]


def test_postgres_list_refund_audit_log_entries_filters_and_paginates(monkeypatch):
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
                    "refund_type": "PARTIAL",
                    "refunded_amount": Decimal("128.00"),
                    "refunded_item_count": 1,
                    "refunded_item_nos": '["I-1"]',
                    "reason": "游客申请退款",
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

    result = PostgresOrderRepository().list_refund_audit_log_entries(
        AdminRefundAuditLogListFilter(
            refund_type="PARTIAL",
            order_no="paid",
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
    assert result.items[0].refunded_item_nos == ["I-1"]
    assert "FROM refund_audit_log ral" in calls[0][0]
    assert "ral.refund_type = %s" in calls[0][0]
    assert "UPPER(ral.order_no) LIKE UPPER(%s)" in calls[0][0]
    assert "UPPER(ral.operator_username) LIKE UPPER(%s)" in calls[0][0]
    assert "ral.created_at::date >= %s" in calls[0][0]
    assert "ral.created_at::date <= %s" in calls[0][0]
    assert calls[0][1] == ("PARTIAL", "%paid%", "%demo%", date(2026, 7, 1), date(2026, 7, 31))
    assert "ORDER BY created_at DESC, id DESC" in calls[1][0]
    assert "LIMIT %s OFFSET %s" in calls[1][0]
    assert calls[1][1] == ("PARTIAL", "%paid%", "%demo%", date(2026, 7, 1), date(2026, 7, 31), 10, 10)


def test_postgres_refund_audit_log_csv_export_uses_parameterized_filters(monkeypatch):
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
                    "refund_type": "PARTIAL",
                    "refunded_amount": Decimal("128.00"),
                    "refunded_item_count": 1,
                    "refunded_item_nos": '["I-1"]',
                    "reason": "游客申请退款",
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

    result = PostgresOrderRepository().list_refund_audit_log_export_rows(
        AdminRefundAuditLogExportFilter(
            refund_type="PARTIAL",
            order_no="paid",
            operator_username="demo",
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 31),
        )
    )

    assert len(result) == 1
    assert result[0].order_no == "O-PAID"
    assert result[0].refunded_item_nos == ["I-1"]
    assert len(calls) == 1
    assert "FROM refund_audit_log ral" in calls[0][0]
    assert "ral.refund_type = %s" in calls[0][0]
    assert "UPPER(ral.order_no) LIKE UPPER(%s)" in calls[0][0]
    assert "UPPER(ral.operator_username) LIKE UPPER(%s)" in calls[0][0]
    assert "ral.created_at::date >= %s" in calls[0][0]
    assert "ral.created_at::date <= %s" in calls[0][0]
    assert "ORDER BY created_at DESC, id DESC" in calls[0][0]
    assert "LIMIT" not in calls[0][0]
    assert "2026-07-01" not in calls[0][0]
    assert "2026-07-31" not in calls[0][0]
    assert calls[0][1] == ("PARTIAL", "%paid%", "%demo%", date(2026, 7, 1), date(2026, 7, 31))


def test_postgres_refund_audit_log_export_rows_apply_optional_row_limit(monkeypatch):
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

    PostgresOrderRepository().list_refund_audit_log_export_rows(
        AdminRefundAuditLogExportFilter(
            refund_type="PARTIAL",
            order_no="paid",
            operator_username="demo",
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 31),
            row_limit=77,
        )
    )

    sql, params = calls[0]
    assert "FROM refund_audit_log ral" in sql
    assert "LIMIT %s" in sql
    assert "77" not in sql
    assert params == ("PARTIAL", "%paid%", "%demo%", date(2026, 7, 1), date(2026, 7, 31), 77)


def test_postgres_partial_refund_rejects_used_item_before_restock_or_updates(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            return {
                "order_id": 1,
                "order_no": "O-USED",
                "order_status": "PAID",
                "payment_status": "PAID",
                "paid_amount": Decimal("128.00"),
            }

        def fetchall(self):
            return [
                {
                    "order_item_id": 10,
                    "item_no": "I-USED",
                    "item_status": "USED",
                    "time_slot_id": 100,
                    "final_price": Decimal("128.00"),
                }
            ]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    try:
        PostgresOrderRepository().refund_order_items("O-USED", ["I-USED"], refund_audit_input())
    except OrderNotRefundableError:
        pass
    else:
        raise AssertionError("used ticket order item must not be partially refundable")

    assert len(calls) == 2
    assert not any("FROM payment_record" in sql for sql, _params in calls)
    assert not any("UPDATE time_slot_quota" in sql for sql, _params in calls)
    assert not any("UPDATE ticket_order_item" in sql for sql, _params in calls)
    assert not any("UPDATE payment_record" in sql for sql, _params in calls)
    assert not any("UPDATE ticket_order\n" in sql for sql, _params in calls)
    assert not any("INSERT INTO refund_audit_log" in sql for sql, _params in calls)


def test_postgres_partial_refund_rejects_order_without_success_payment_record_before_side_effects(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "SELECT" in calls[-1][0] and "FROM ticket_order\n" in calls[-1][0]:
                return {
                    "order_id": 1,
                    "order_no": "O-PAID",
                    "order_status": "PAID",
                    "payment_status": "PAID",
                    "paid_amount": Decimal("128.00"),
                }
            if "SELECT" in calls[-1][0] and "FROM payment_record\n" in calls[-1][0]:
                return None
            return None

        def fetchall(self):
            return [
                {
                    "order_item_id": 10,
                    "item_no": "I-1",
                    "item_status": "UNUSED",
                    "time_slot_id": 100,
                    "final_price": Decimal("128.00"),
                }
            ]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    try:
        PostgresOrderRepository().refund_order_items("O-PAID", ["I-1"], refund_audit_input())
    except OrderNotRefundableError:
        pass
    else:
        raise AssertionError("partial refund without a successful payment record must not be refundable")

    assert len(calls) == 3
    assert "FROM payment_record" in calls[2][0]
    assert "FOR UPDATE" in calls[2][0]
    assert not any("UPDATE time_slot_quota" in sql for sql, _params in calls)
    assert not any("UPDATE ticket_order_item" in sql for sql, _params in calls)
    assert not any("UPDATE payment_record" in sql for sql, _params in calls)
    assert not any("UPDATE ticket_order\n" in sql for sql, _params in calls)
    assert not any("INSERT INTO refund_audit_log" in sql for sql, _params in calls)


def test_postgres_partial_refund_rejects_quota_restock_condition_failure_before_order_updates(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "SELECT" in calls[-1][0] and "FROM ticket_order\n" in calls[-1][0]:
                return {
                    "order_id": 1,
                    "order_no": "O-PAID",
                    "order_status": "PAID",
                    "payment_status": "PAID",
                    "paid_amount": Decimal("128.00"),
                }
            if "SELECT" in calls[-1][0] and "FROM payment_record\n" in calls[-1][0]:
                return {"payment_record_id": 200}
            if "UPDATE time_slot_quota" in calls[-1][0]:
                return None
            return None

        def fetchall(self):
            return [
                {
                    "order_item_id": 10,
                    "item_no": "I-1",
                    "item_status": "UNUSED",
                    "time_slot_id": 100,
                    "final_price": Decimal("128.00"),
                }
            ]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    try:
        PostgresOrderRepository().refund_order_items("O-PAID", ["I-1"], refund_audit_input())
    except OrderNotRefundableError:
        pass
    else:
        raise AssertionError("quota restock condition failure must not be partially refundable")

    assert len(calls) == 4
    assert "UPDATE time_slot_quota" in calls[3][0]
    assert not any("UPDATE ticket_order_item" in sql for sql, _params in calls)
    assert not any("UPDATE payment_record" in sql for sql, _params in calls)
    assert not any("UPDATE ticket_order\n" in sql for sql, _params in calls)
    assert not any("INSERT INTO refund_audit_log" in sql for sql, _params in calls)


def test_postgres_refund_rejects_used_item_before_restock_or_order_updates(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            return {
                "order_id": 1,
                "order_no": "O-USED",
                "order_status": "PAID",
                "payment_status": "PAID",
                "paid_amount": Decimal("128.00"),
            }

        def fetchall(self):
            return [{"order_item_id": 10, "item_status": "USED", "time_slot_id": 100, "final_price": Decimal("128.00")}]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    try:
        PostgresOrderRepository().refund_order("O-USED", refund_audit_input())
    except OrderNotRefundableError:
        pass
    else:
        raise AssertionError("used ticket order must not be refundable")

    assert len(calls) == 2
    assert not any("UPDATE time_slot_quota" in sql for sql, _params in calls)
    assert not any("UPDATE ticket_order_item" in sql for sql, _params in calls)
    assert not any("UPDATE payment_record" in sql for sql, _params in calls)
    assert not any("UPDATE ticket_order\n" in sql for sql, _params in calls)
    assert not any("INSERT INTO refund_audit_log" in sql for sql, _params in calls)


def test_postgres_refund_rejects_quota_restock_condition_failure_before_order_updates(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "SELECT" in calls[-1][0] and "FROM ticket_order\n" in calls[-1][0]:
                return {
                    "order_id": 1,
                    "order_no": "O-PAID",
                    "order_status": "PAID",
                    "payment_status": "PAID",
                    "paid_amount": Decimal("128.00"),
                }
            if "SELECT" in calls[-1][0] and "FROM payment_record\n" in calls[-1][0]:
                return {"payment_record_id": 200}
            if "UPDATE time_slot_quota" in calls[-1][0]:
                return None
            return None

        def fetchall(self):
            return [{"order_item_id": 10, "item_status": "UNUSED", "time_slot_id": 100, "final_price": Decimal("128.00")}]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    try:
        PostgresOrderRepository().refund_order("O-PAID", refund_audit_input())
    except OrderNotRefundableError:
        pass
    else:
        raise AssertionError("quota restock condition failure must not be refundable")

    assert len(calls) == 4
    assert "UPDATE time_slot_quota" in calls[3][0]
    assert not any("UPDATE ticket_order_item" in sql for sql, _params in calls)
    assert not any("UPDATE payment_record" in sql for sql, _params in calls)
    assert not any("UPDATE ticket_order\n" in sql for sql, _params in calls)
    assert not any("INSERT INTO refund_audit_log" in sql for sql, _params in calls)


def test_postgres_refund_rejects_order_without_success_payment_record_before_side_effects(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "SELECT" in calls[-1][0] and "FROM ticket_order\n" in calls[-1][0]:
                return {
                    "order_id": 1,
                    "order_no": "O-PAID",
                    "order_status": "PAID",
                    "payment_status": "PAID",
                    "paid_amount": Decimal("128.00"),
                }
            if "SELECT" in calls[-1][0] and "FROM payment_record\n" in calls[-1][0]:
                return None
            return None

        def fetchall(self):
            return [{"order_item_id": 10, "item_status": "UNUSED", "time_slot_id": 100, "final_price": Decimal("128.00")}]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    try:
        PostgresOrderRepository().refund_order("O-PAID", refund_audit_input())
    except OrderNotRefundableError:
        pass
    else:
        raise AssertionError("order without a successful payment record must not be refundable")

    assert len(calls) == 3
    assert "FROM payment_record" in calls[2][0]
    assert "FOR UPDATE" in calls[2][0]
    assert not any("UPDATE time_slot_quota" in sql for sql, _params in calls)
    assert not any("UPDATE ticket_order_item" in sql for sql, _params in calls)
    assert not any("UPDATE payment_record" in sql for sql, _params in calls)
    assert not any("UPDATE ticket_order\n" in sql for sql, _params in calls)
    assert not any("INSERT INTO refund_audit_log" in sql for sql, _params in calls)
