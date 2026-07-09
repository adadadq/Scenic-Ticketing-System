from datetime import UTC, date, datetime, time
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

import app.repositories.orders as order_repository_module
from app.core.security import hash_secret
from app.main import create_app
from app.repositories.auth import SessionVisitorRecord, VisitorRecord, get_auth_repository
from app.repositories.orders import (
    OrderCancelStateError,
    OrderCreateItemRecord,
    OrderRecord,
    PostgresOrderRepository,
    get_order_repository,
)


class FakeAuthRepository:
    def __init__(self, visitor: VisitorRecord):
        self.visitor = visitor
        self.session_token = "session-token"
        self.csrf_token = "csrf-token"

    def find_session_visitor(self, session_token_hash: str, _now: datetime) -> SessionVisitorRecord | None:
        if session_token_hash != hash_secret(self.session_token):
            return None
        return SessionVisitorRecord(
            session_id=1,
            visitor=self.visitor,
            csrf_token_hash=hash_secret(self.csrf_token),
            expires_at=datetime(2026, 7, 1, 18, 0, tzinfo=UTC),
            revoked_at=None,
        )

    def touch_session(self, _session_id: int) -> None:
        pass


class FakeMyOrdersRepository:
    def __init__(self):
        self.orders = {
            "O-PENDING": self.order("O-PENDING", visitor_id=1, status="CREATED", payment_status="UNPAID"),
            "O-PAID": self.order(
                "O-PAID",
                visitor_id=1,
                status="PAID",
                payment_status="PAID",
                item_status="UNUSED",
                ticket_code="TKRANDOMABC123",
            ),
            "O-OTHER": self.order("O-OTHER", visitor_id=2, status="CREATED", payment_status="UNPAID"),
        }
        self.quota_sold = 0

    def item(self, item_no: str, item_status: str = "PENDING_PAYMENT", ticket_code: str | None = None) -> OrderCreateItemRecord:
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
        visitor_id: int,
        status: str,
        payment_status: str,
        item_status: str = "PENDING_PAYMENT",
        ticket_code: str | None = None,
    ) -> OrderRecord:
        return OrderRecord(
            order_id=len(order_no),
            order_no=order_no,
            visitor_id=visitor_id,
            buyer_name="张三",
            buyer_phone="13911112222",
            order_status=status,
            payment_status=payment_status,
            total_amount=Decimal("128.00"),
            payable_amount=Decimal("128.00"),
            order_time=datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
            items=[self.item(f"I-{order_no}", item_status=item_status, ticket_code=ticket_code)],
        )

    def list_orders_for_visitor(self, visitor_id: int, order_status: str | None = None) -> list[OrderRecord]:
        orders = [order for order in self.orders.values() if order.visitor_id == visitor_id]
        if order_status:
            orders = [order for order in orders if order.order_status == order_status]
        return orders

    def get_order_for_visitor(self, visitor_id: int, order_no: str) -> OrderRecord | None:
        order = self.orders.get(order_no)
        if order is None or order.visitor_id != visitor_id:
            return None
        return order

    def cancel_order(self, order_no: str, visitor_id: int) -> OrderRecord | None:
        order = self.get_order_for_visitor(visitor_id, order_no)
        if order is None:
            return None
        if order.order_status != "CREATED" or order.payment_status != "UNPAID":
            raise OrderCancelStateError
        cancelled_items = [
            OrderCreateItemRecord(
                item_no=item.item_no,
                product_id=item.product_id,
                ticket_type_id=item.ticket_type_id,
                product_name=item.product_name,
                ticket_name=item.ticket_name,
                time_slot_id=item.time_slot_id,
                visit_date=item.visit_date,
                slot_start_time=item.slot_start_time,
                slot_end_time=item.slot_end_time,
                original_price=item.original_price,
                final_price=item.final_price,
                item_status="CANCELLED",
                ticket_code=item.ticket_code,
            )
            for item in order.items
        ]
        cancelled = OrderRecord(
            order_id=order.order_id,
            order_no=order.order_no,
            visitor_id=order.visitor_id,
            buyer_name=order.buyer_name,
            buyer_phone=order.buyer_phone,
            order_status="CANCELLED",
            payment_status=order.payment_status,
            total_amount=order.total_amount,
            payable_amount=order.payable_amount,
            order_time=order.order_time,
            items=cancelled_items,
        )
        self.orders[order_no] = cancelled
        return cancelled


def registered_visitor(visitor_id: int = 1) -> VisitorRecord:
    return VisitorRecord(
        id=visitor_id,
        visitor_name="张三",
        id_type="ID_CARD",
        id_number="11010519491231002X",
        phone="13911112222",
        visitor_scope="REGISTERED",
    )


def build_client(auth_repo: FakeAuthRepository, order_repo: FakeMyOrdersRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repo
    app.dependency_overrides[get_order_repository] = lambda: order_repo
    client = TestClient(app)
    client.cookies.set("scenic_session", auth_repo.session_token)
    client.cookies.set("scenic_csrf", auth_repo.csrf_token)
    return client


def csrf_headers(client: TestClient) -> dict[str, str]:
    token = client.cookies.get("scenic_csrf")
    assert token
    return {"x-csrf-token": token}


def test_pending_order_can_be_cancelled_without_touching_inventory():
    order_repo = FakeMyOrdersRepository()
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)

    response = client.post("/api/orders/O-PENDING/cancel", headers=csrf_headers(client))

    data = response.json()["data"]
    assert response.status_code == 200
    assert data["orderStatus"] == "CANCELLED"
    assert data["paymentStatus"] == "UNPAID"
    assert data["buyerPhone"] == "139****2222"
    assert data["items"][0]["itemStatus"] == "CANCELLED"
    assert order_repo.quota_sold == 0


def test_paid_order_cancel_returns_business_error():
    order_repo = FakeMyOrdersRepository()
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)

    response = client.post("/api/orders/O-PAID/cancel", headers=csrf_headers(client))

    assert response.status_code == 409
    assert response.json()["code"] == "ORDER_NOT_CANCELABLE"


def test_failed_payment_status_order_cancel_returns_business_error():
    order_repo = FakeMyOrdersRepository()
    order_repo.orders["O-FAILED"] = order_repo.order(
        "O-FAILED",
        visitor_id=1,
        status="CREATED",
        payment_status="FAILED",
    )
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)

    response = client.post("/api/orders/O-FAILED/cancel", headers=csrf_headers(client))

    assert response.status_code == 409
    assert response.json()["code"] == "ORDER_NOT_CANCELABLE"
    assert order_repo.orders["O-FAILED"].order_status == "CREATED"
    assert order_repo.orders["O-FAILED"].payment_status == "FAILED"
    assert order_repo.quota_sold == 0


def test_cancelling_another_visitor_order_returns_not_found():
    order_repo = FakeMyOrdersRepository()
    client = build_client(FakeAuthRepository(registered_visitor(visitor_id=1)), order_repo)

    response = client.post(
        "/api/orders/O-OTHER/cancel",
        headers=csrf_headers(client) | {"x-request-id": "req-cancel-other-order"},
    )

    data = response.json()
    assert response.status_code == 404
    assert data == {
        "success": False,
        "code": "ORDER_NOT_FOUND",
        "message": "订单不存在或无权限访问",
        "request_id": "req-cancel-other-order",
    }
    assert response.headers["x-request-id"] == "req-cancel-other-order"
    assert "O-OTHER" not in str(data)
    assert order_repo.orders["O-OTHER"].order_status == "CREATED"


def test_cancel_requires_csrf():
    order_repo = FakeMyOrdersRepository()
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)

    response = client.post("/api/orders/O-PENDING/cancel")

    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_INVALID"


def test_cancel_rejects_csrf_token_not_bound_to_session():
    order_repo = FakeMyOrdersRepository()
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)
    client.cookies.set("scenic_csrf", "rotated-csrf")

    response = client.post(
        "/api/orders/O-PENDING/cancel",
        headers={"x-csrf-token": "rotated-csrf"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_INVALID"
    assert order_repo.orders["O-PENDING"].order_status == "CREATED"


def test_my_orders_only_returns_current_visitor_orders_and_supports_status_filter():
    order_repo = FakeMyOrdersRepository()
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)

    all_orders = client.get("/api/me/orders")
    paid_orders = client.get("/api/me/orders?status=paid")
    empty_status_orders = client.get("/api/me/orders?status=")

    assert all_orders.status_code == 200
    all_order_data = all_orders.json()["data"]
    assert {order["orderNo"] for order in all_order_data} == {"O-PENDING", "O-PAID"}
    assert all(order["buyerPhone"] == "139****2222" for order in all_order_data)
    assert all("visitorId" not in order and "idNumber" not in order for order in all_order_data)
    assert paid_orders.status_code == 200
    assert [order["orderNo"] for order in paid_orders.json()["data"]] == ["O-PAID"]
    assert empty_status_orders.status_code == 200
    assert {order["orderNo"] for order in empty_status_orders.json()["data"]} == {"O-PENDING", "O-PAID"}


def test_phone_masking_fails_closed_for_legacy_malformed_phone_values():
    order_repo = FakeMyOrdersRepository()
    order_repo.orders["O-PENDING"] = order_repo.order("O-PENDING", visitor_id=1, status="CREATED", payment_status="UNPAID")
    legacy_order = order_repo.orders["O-PENDING"]
    order_repo.orders["O-PENDING"] = OrderRecord(
        order_id=legacy_order.order_id,
        order_no=legacy_order.order_no,
        visitor_id=legacy_order.visitor_id,
        buyer_name=legacy_order.buyer_name,
        buyer_phone="123456",
        order_status=legacy_order.order_status,
        payment_status=legacy_order.payment_status,
        total_amount=legacy_order.total_amount,
        payable_amount=legacy_order.payable_amount,
        order_time=legacy_order.order_time,
        items=legacy_order.items,
    )
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)

    response = client.get("/api/me/orders/O-PENDING")

    assert response.status_code == 200
    assert response.json()["data"]["buyerPhone"] == "****3456"


@pytest.mark.parametrize(
    ("invalid_status", "request_id"),
    [
        ("DELETED", "req-status-filter-invalid"),
        ("THIS_STATUS_IS_LONGER_THAN_32_CHARS_1234567890", "req-status-filter-too-long"),
    ],
)
def test_invalid_my_orders_status_filter_returns_validation_error(invalid_status: str, request_id: str):
    order_repo = FakeMyOrdersRepository()
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)

    response = client.get(
        f"/api/me/orders?status={invalid_status}",
        headers={"x-request-id": request_id},
    )

    data = response.json()
    assert response.status_code == 422
    assert data == {
        "success": False,
        "code": "ORDER_STATUS_INVALID",
        "message": "订单状态筛选不合法",
        "request_id": request_id,
    }
    assert response.headers["x-request-id"] == request_id
    assert invalid_status not in str(data)


def test_paid_order_detail_includes_ticket_code_and_time_amount_status_fields():
    order_repo = FakeMyOrdersRepository()
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)

    response = client.get("/api/me/orders/O-PAID")

    item = response.json()["data"]["items"][0]
    assert response.status_code == 200
    assert item["ticketCode"] == "TKRANDOMABC123"
    assert item["slotStartTime"] == "08:30:00"
    assert item["slotEndTime"] == "10:30:00"
    assert item["finalPrice"] == "128.00"
    assert item["itemStatus"] == "UNUSED"


@pytest.mark.parametrize(
    ("order_no", "request_id"),
    [
        ("O-OTHER", "req-detail-other-visitor"),
        ("O-MISSING", "req-detail-missing-order"),
    ],
)
def test_order_detail_not_found_or_another_visitor_returns_same_error(order_no: str, request_id: str):
    order_repo = FakeMyOrdersRepository()
    client = build_client(FakeAuthRepository(registered_visitor(visitor_id=1)), order_repo)

    response = client.get(
        f"/api/me/orders/{order_no}",
        headers={"x-request-id": request_id},
    )

    data = response.json()
    assert response.status_code == 404
    assert data == {
        "success": False,
        "code": "ORDER_NOT_FOUND",
        "message": "订单不存在或无权限访问",
        "request_id": request_id,
    }
    assert response.headers["x-request-id"] == request_id
    assert order_no not in str(data)


class ScriptedCursor:
    def __init__(self, result):
        self.result = result

    def fetchone(self):
        return self.result

    def fetchall(self):
        return self.result


class ScriptedConnection:
    def __init__(self, results: list):
        self.results = results
        self.queries: list[tuple[str, tuple[object, ...] | None]] = []

    def __enter__(self):
        return self

    def __exit__(self, *_exc_info):
        return False

    def execute(self, query: str, params: tuple[object, ...] | None = None) -> ScriptedCursor:
        self.queries.append((query, params))
        return ScriptedCursor(self.results.pop(0))


def test_postgres_list_orders_loads_items_for_frontend_summary(monkeypatch):
    order_row = {
        "order_id": 1,
        "order_no": "O-PAID",
        "visitor_id": 1,
        "buyer_name": "张三",
        "buyer_phone": "13911112222",
        "order_status": "PAID",
        "payment_status": "PAID",
        "total_amount": Decimal("128.00"),
        "payable_amount": Decimal("128.00"),
        "order_time": datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
    }
    paid_item_row = {
        "item_no": "I001",
        "product_id": 1,
        "ticket_type_id": 10,
        "product_name": "金龙桥至旧县成人票",
        "ticket_name": "遇龙河成人票",
        "time_slot_id": 100,
        "visit_date": date(2026, 7, 1),
        "slot_start_time": time(8, 30),
        "slot_end_time": time(10, 30),
        "original_price": Decimal("168.00"),
        "final_price": Decimal("128.00"),
        "item_status": "UNUSED",
        "ticket_code": "TKRANDOMABC123",
    }
    connection = ScriptedConnection(results=[[order_row], [paid_item_row]])
    monkeypatch.setattr(order_repository_module, "connect_db", lambda: connection)

    orders = PostgresOrderRepository().list_orders_for_visitor(1, order_status="PAID")

    assert len(orders) == 1
    assert orders[0].order_no == "O-PAID"
    assert orders[0].items[0].product_name == "金龙桥至旧县成人票"
    assert orders[0].items[0].slot_start_time == time(8, 30)
    assert orders[0].items[0].ticket_code == "TKRANDOMABC123"
    assert connection.queries[0][1] == (1, "PAID")
    assert connection.queries[1][1] == (1,)
    assert "FROM ticket_order_item" in connection.queries[1][0]
    assert "JOIN route_product rp ON rp.id = toi.product_id" in connection.queries[1][0]


def test_postgres_cancel_locks_order_updates_pending_items_and_does_not_touch_inventory(monkeypatch):
    order_row = {
        "order_id": 1,
        "order_no": "O-PENDING",
        "visitor_id": 1,
        "buyer_name": "张三",
        "buyer_phone": "13911112222",
        "order_status": "CREATED",
        "payment_status": "UNPAID",
        "total_amount": Decimal("128.00"),
        "payable_amount": Decimal("128.00"),
        "order_time": datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
    }
    cancelled_row = order_row | {"order_status": "CANCELLED"}
    cancelled_item_row = {
        "item_no": "I001",
        "product_id": 1,
        "ticket_type_id": 10,
        "product_name": "金龙桥至旧县成人票",
        "ticket_name": "遇龙河成人票",
        "time_slot_id": 100,
        "visit_date": date(2026, 7, 1),
        "slot_start_time": time(8, 30),
        "slot_end_time": time(10, 30),
        "original_price": Decimal("168.00"),
        "final_price": Decimal("128.00"),
        "item_status": "CANCELLED",
        "ticket_code": None,
    }
    connection = ScriptedConnection(results=[order_row, None, None, cancelled_row, [cancelled_item_row]])
    monkeypatch.setattr(order_repository_module, "connect_db", lambda: connection)

    order = PostgresOrderRepository().cancel_order("O-PENDING", visitor_id=1)

    queries = "\n".join(query for query, _params in connection.queries)
    assert order.order_status == "CANCELLED"
    assert "FOR UPDATE" in connection.queries[0][0]
    assert "UPDATE ticket_order_item" in queries
    assert "item_status = 'CANCELLED'" in queries
    assert "UPDATE ticket_order" in queries
    assert "cancel_time = CURRENT_TIMESTAMP" in queries
    assert "UPDATE time_slot_quota" not in queries


def test_postgres_cancel_rejects_paid_order_before_updates(monkeypatch):
    paid_order_row = {
        "order_id": 1,
        "order_no": "O-PAID",
        "visitor_id": 1,
        "buyer_name": "张三",
        "buyer_phone": "13911112222",
        "order_status": "PAID",
        "payment_status": "PAID",
        "total_amount": Decimal("128.00"),
        "payable_amount": Decimal("128.00"),
        "order_time": datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
    }
    connection = ScriptedConnection(results=[paid_order_row])
    monkeypatch.setattr(order_repository_module, "connect_db", lambda: connection)

    with pytest.raises(OrderCancelStateError):
        PostgresOrderRepository().cancel_order("O-PAID", visitor_id=1)

    assert len(connection.queries) == 1
    assert "FOR UPDATE" in connection.queries[0][0]


def test_postgres_cancel_rejects_failed_payment_status_before_updates(monkeypatch):
    failed_payment_order_row = {
        "order_id": 1,
        "order_no": "O-FAILED",
        "visitor_id": 1,
        "buyer_name": "张三",
        "buyer_phone": "13911112222",
        "order_status": "CREATED",
        "payment_status": "FAILED",
        "total_amount": Decimal("128.00"),
        "payable_amount": Decimal("128.00"),
        "order_time": datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
    }
    connection = ScriptedConnection(results=[failed_payment_order_row])
    monkeypatch.setattr(order_repository_module, "connect_db", lambda: connection)

    with pytest.raises(OrderCancelStateError):
        PostgresOrderRepository().cancel_order("O-FAILED", visitor_id=1)

    queries = "\n".join(query for query, _params in connection.queries)
    assert len(connection.queries) == 1
    assert "FOR UPDATE" in connection.queries[0][0]
    assert "UPDATE ticket_order_item" not in queries
    assert "UPDATE ticket_order" not in queries
    assert "UPDATE time_slot_quota" not in queries
