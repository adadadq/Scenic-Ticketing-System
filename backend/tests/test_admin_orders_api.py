from datetime import UTC, date, datetime, time
from decimal import Decimal

from fastapi.testclient import TestClient

import app.repositories.orders as order_repository_module
from app.main import create_app
from app.repositories.auth import get_auth_repository
from app.repositories.orders import (
    AdminOrderListFilter,
    AdminOrderListRecord,
    AdminOrderSummaryRecord,
    OrderCreateItemRecord,
    OrderRecord,
    PostgresOrderRepository,
    get_order_repository,
)

from test_admin_auth_api import FakeAuthRepository, admin_login_payload, seed_enabled_admin
from test_auth_api import csrf_headers


class FakeAdminOrdersRepository:
    def __init__(self):
        self.orders = {
            "O-PAID": self.order(
                "O-PAID",
                order_id=1,
                visitor_id=10,
                order_status="PAID",
                payment_status="PAID",
                item_status="UNUSED",
                ticket_code="TKRANDOMABC123",
                buyer_phone="13911112222",
            ),
            "O-CREATED": self.order(
                "O-CREATED",
                order_id=2,
                visitor_id=11,
                order_status="CREATED",
                payment_status="UNPAID",
                item_status="PENDING_PAYMENT",
                ticket_code=None,
                buyer_phone="13800009999",
            ),
        }
        self.last_filters: AdminOrderListFilter | None = None

    def item(self, item_no: str, item_status: str, ticket_code: str | None) -> OrderCreateItemRecord:
        return OrderCreateItemRecord(
            item_no=item_no,
            product_id=1,
            ticket_type_id=10,
            product_name="金龙桥至旧县成人票",
            ticket_name="遇龙河成人票",
            time_slot_id=100,
            visit_date=date(2026, 7, 1),
            slot_start_time=time(8, 30),
            slot_end_time=time(10, 30),
            original_price=Decimal("168.00"),
            final_price=Decimal("128.00"),
            item_status=item_status,
            ticket_code=ticket_code,
        )

    def order(
        self,
        order_no: str,
        order_id: int,
        visitor_id: int,
        order_status: str,
        payment_status: str,
        item_status: str,
        ticket_code: str | None,
        buyer_phone: str,
    ) -> OrderRecord:
        return OrderRecord(
            order_id=order_id,
            order_no=order_no,
            visitor_id=visitor_id,
            buyer_name="张三",
            buyer_phone=buyer_phone,
            order_status=order_status,
            payment_status=payment_status,
            total_amount=Decimal("128.00"),
            payable_amount=Decimal("128.00"),
            order_time=datetime(2026, 7, order_id, 9, 0, tzinfo=UTC),
            items=[self.item(f"I-{order_no}", item_status, ticket_code)],
        )

    def list_orders_for_admin(self, filters: AdminOrderListFilter) -> AdminOrderListRecord:
        self.last_filters = filters
        orders = list(self.orders.values())
        if filters.status:
            orders = [order for order in orders if order.order_status == filters.status]
        if filters.payment_status:
            orders = [order for order in orders if order.payment_status == filters.payment_status]
        if filters.order_no:
            orders = [order for order in orders if filters.order_no.upper() in order.order_no.upper()]
        if filters.buyer_phone:
            if filters.buyer_phone.isdigit() and len(filters.buyer_phone) == 4:
                orders = [order for order in orders if order.buyer_phone.endswith(filters.buyer_phone)]
            else:
                orders = [order for order in orders if order.buyer_phone == filters.buyer_phone]

        total = len(orders)
        start = (filters.page - 1) * filters.page_size
        page_orders = orders[start : start + filters.page_size]
        return AdminOrderListRecord(
            items=[
                AdminOrderSummaryRecord(
                    order_id=order.order_id,
                    order_no=order.order_no,
                    visitor_id=order.visitor_id,
                    buyer_name=order.buyer_name,
                    buyer_phone=order.buyer_phone,
                    order_status=order.order_status,
                    payment_status=order.payment_status,
                    total_amount=order.total_amount,
                    payable_amount=order.payable_amount,
                    order_time=order.order_time,
                    item_count=len(order.items),
                )
                for order in page_orders
            ],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )

    def get_order_for_admin(self, order_no: str) -> OrderRecord | None:
        return self.orders.get(order_no)


def build_client(auth_repo: FakeAuthRepository, order_repo: FakeAdminOrdersRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repo
    app.dependency_overrides[get_order_repository] = lambda: order_repo
    return TestClient(app)


def login_admin(client: TestClient, auth_repo: FakeAuthRepository) -> None:
    seed_enabled_admin(auth_repo)
    response = client.post(
        "/api/admin/auth/login",
        json=admin_login_payload(),
        headers=csrf_headers(client),
    )
    assert response.status_code == 200


def login_visitor(client: TestClient) -> None:
    response = client.post(
        "/api/auth/visitor/register",
        json={"username": "demo_visitor", "password": "Visitor123", "phone": "13911112222"},
        headers=csrf_headers(client),
    )
    assert response.status_code == 200


def test_admin_can_list_orders_with_filters_and_masked_phone():
    auth_repo = FakeAuthRepository()
    order_repo = FakeAdminOrdersRepository()
    client = build_client(auth_repo, order_repo)
    login_admin(client, auth_repo)

    response = client.get(
        "/api/admin/orders",
        params={
            "status": "paid",
            "paymentStatus": "paid",
            "orderNo": "paid",
            "buyerPhone": "2222",
            "page": 1,
            "pageSize": 1,
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["data"]["total"] == 1
    assert body["data"]["page"] == 1
    assert body["data"]["pageSize"] == 1
    assert body["data"]["items"] == [
        {
            "orderNo": "O-PAID",
            "visitorId": 10,
            "buyerName": "张三",
            "buyerPhoneMasked": "139****2222",
            "orderStatus": "PAID",
            "paymentStatus": "PAID",
            "totalAmount": "128.00",
            "payableAmount": "128.00",
            "orderTime": "2026-07-01T09:00:00Z",
            "itemCount": 1,
        }
    ]
    assert "buyerPhone" not in body["data"]["items"][0]
    assert "13911112222" not in response.text
    assert order_repo.last_filters == AdminOrderListFilter(
        status="PAID",
        payment_status="PAID",
        order_no="paid",
        buyer_phone="2222",
        page=1,
        page_size=1,
    )
    assert auth_repo.touched_sessions == []


def test_admin_can_get_order_detail_without_internal_sensitive_fields():
    auth_repo = FakeAuthRepository()
    order_repo = FakeAdminOrdersRepository()
    client = build_client(auth_repo, order_repo)
    login_admin(client, auth_repo)

    response = client.get("/api/admin/orders/O-PAID")

    data = response.json()["data"]
    assert response.status_code == 200
    assert data["orderNo"] == "O-PAID"
    assert data["buyerPhoneMasked"] == "139****2222"
    assert data["items"][0]["ticketCode"] == "TKRANDOMABC123"
    assert "buyerPhone" not in data
    assert "13911112222" not in response.text
    assert "idNumber" not in response.text
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()


def test_admin_orders_require_admin_session_and_reject_visitor_session():
    auth_repo = FakeAuthRepository()
    order_repo = FakeAdminOrdersRepository()
    client = build_client(auth_repo, order_repo)

    anonymous = client.get("/api/admin/orders")
    anonymous_detail = client.get("/api/admin/orders/O-PAID")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"
    assert anonymous_detail.status_code == 401
    assert anonymous_detail.json()["code"] == "ADMIN_AUTH_REQUIRED"

    login_visitor(client)
    visitor_list = client.get("/api/admin/orders")
    visitor_detail = client.get("/api/admin/orders/O-PAID")

    assert visitor_list.status_code == 403
    assert visitor_list.json()["code"] == "ADMIN_FORBIDDEN"
    assert visitor_detail.status_code == 403
    assert visitor_detail.json()["code"] == "ADMIN_FORBIDDEN"


def test_admin_order_detail_path_rejects_overlong_order_no_before_repository_lookup():
    auth_repo = FakeAuthRepository()
    order_repo = FakeAdminOrdersRepository()
    client = build_client(auth_repo, order_repo)
    login_admin(client, auth_repo)

    response = client.get(f"/api/admin/orders/{'O' * 65}")

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_admin_order_filters_use_specific_error_codes():
    auth_repo = FakeAuthRepository()
    order_repo = FakeAdminOrdersRepository()
    client = build_client(auth_repo, order_repo)
    login_admin(client, auth_repo)

    invalid_status = client.get("/api/admin/orders", params={"status": "DELETED"})
    invalid_payment = client.get("/api/admin/orders", params={"paymentStatus": "PENDING"})

    assert invalid_status.status_code == 422
    assert invalid_status.json()["code"] == "ADMIN_ORDER_STATUS_INVALID"
    assert invalid_payment.status_code == 422
    assert invalid_payment.json()["code"] == "ADMIN_PAYMENT_STATUS_INVALID"


def test_admin_order_detail_not_found_uses_admin_error_code():
    auth_repo = FakeAuthRepository()
    order_repo = FakeAdminOrdersRepository()
    client = build_client(auth_repo, order_repo)
    login_admin(client, auth_repo)

    response = client.get("/api/admin/orders/O-MISSING")

    assert response.status_code == 404
    assert response.json()["code"] == "ADMIN_ORDER_NOT_FOUND"
    assert response.json()["message"] == "订单不存在"


def test_postgres_admin_order_list_uses_parameterized_filters(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            return {"total": 0}

        def fetchall(self):
            return []

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    repository = PostgresOrderRepository()
    result = repository.list_orders_for_admin(
        AdminOrderListFilter(
            status="PAID",
            payment_status="PAID",
            order_no="O-PAID",
            buyer_phone="2222",
            page=2,
            page_size=10,
        )
    )

    assert result.total == 0
    assert len(calls) == 2
    for sql, _params in calls:
        assert "o.order_status = %s" in sql
        assert "o.payment_status = %s" in sql
        assert "UPPER(o.order_no) LIKE UPPER(%s)" in sql
        assert "o.buyer_phone LIKE %s" in sql
        assert "PAID" not in sql
        assert "O-PAID" not in sql
        assert "2222" not in sql
    assert calls[0][1] == ("PAID", "PAID", "%O-PAID%", "%2222")
    assert calls[1][1] == ("PAID", "PAID", "%O-PAID%", "%2222", 10, 10)
