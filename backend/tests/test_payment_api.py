from datetime import UTC, datetime, time, date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

import app.repositories.orders as order_repository_module
from app.core.security import hash_secret
from app.main import create_app
from app.repositories.auth import SessionVisitorRecord, VisitorRecord, get_auth_repository
from app.repositories.orders import (
    OrderCreateItemRecord,
    OrderPaymentStateError,
    OrderQuotaNotEnoughError,
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


class FakePaymentRepository:
    def __init__(
        self,
        visitor_id: int,
        quota_remaining: int = 5,
        fail_after_stock: bool = False,
        unhandled_error_text: str | None = None,
        expire_on_call: bool = False,
    ):
        self.quota_remaining = quota_remaining
        self.quota_sold = 0
        self.fail_after_stock = fail_after_stock
        self.unhandled_error_text = unhandled_error_text
        self.expire_on_call = expire_on_call
        self.payments: set[tuple[str, str]] = set()
        self.order = OrderRecord(
            order_id=1,
            order_no="O202607010900000001",
            visitor_id=visitor_id,
            buyer_name="张三",
            buyer_phone="13911112222",
            order_status="CREATED",
            payment_status="UNPAID",
            total_amount=Decimal("256.00"),
            payable_amount=Decimal("256.00"),
            order_time=datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
            items=[
                self.item("I001"),
                self.item("I002"),
            ],
        )

    def expire_unpaid_orders(self, visitor_id: int, expired_before: datetime) -> int:
        if (
            self.expire_on_call
            and self.order.visitor_id == visitor_id
            and self.order.order_status == "CREATED"
            and self.order.payment_status == "UNPAID"
            and self.order.order_time <= expired_before
        ):
            self.order = OrderRecord(
                order_id=self.order.order_id,
                order_no=self.order.order_no,
                visitor_id=self.order.visitor_id,
                buyer_name=self.order.buyer_name,
                buyer_phone=self.order.buyer_phone,
                order_status="CANCELLED",
                payment_status=self.order.payment_status,
                total_amount=self.order.total_amount,
                payable_amount=self.order.payable_amount,
                order_time=self.order.order_time,
                items=[
                    self.item(item.item_no, status="CANCELLED" if item.item_status == "PENDING_PAYMENT" else item.item_status)
                    for item in self.order.items
                ],
            )
            return 1
        return 0

    def item(self, item_no: str, status: str = "PENDING_PAYMENT", ticket_code: str | None = None) -> OrderCreateItemRecord:
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
            item_status=status,
            ticket_code=ticket_code,
        )

    def pay_order(
        self,
        order_no: str,
        visitor_id: int,
        idempotency_key: str,
        payment_no: str,
        transaction_no: str,
        ticket_code_factory,
    ) -> OrderRecord | None:
        if self.unhandled_error_text:
            raise RuntimeError(self.unhandled_error_text)
        if order_no != self.order.order_no or visitor_id != self.order.visitor_id:
            return None
        payment_key = (self.order.order_no, idempotency_key)
        if payment_key in self.payments or self.order.order_status == "PAID":
            return self.order
        if self.order.order_status != "CREATED" or self.order.payment_status != "UNPAID":
            raise OrderPaymentStateError
        quantity = len(self.order.items)
        if self.quota_remaining < quantity:
            raise OrderQuotaNotEnoughError

        sold_before = self.quota_sold
        order_before = self.order
        self.quota_sold += quantity
        self.quota_remaining -= quantity
        if self.fail_after_stock:
            self.quota_sold = sold_before
            self.quota_remaining += quantity
            self.order = order_before
            raise OrderPaymentStateError

        paid_items = [
            self.item(item.item_no, status="UNUSED", ticket_code=ticket_code_factory())
            for item in self.order.items
        ]
        self.order = OrderRecord(
            order_id=self.order.order_id,
            order_no=self.order.order_no,
            visitor_id=self.order.visitor_id,
            buyer_name=self.order.buyer_name,
            buyer_phone=self.order.buyer_phone,
            order_status="PAID",
            payment_status="PAID",
            total_amount=self.order.total_amount,
            payable_amount=self.order.payable_amount,
            order_time=self.order.order_time,
            items=paid_items,
        )
        self.payments.add(payment_key)
        assert payment_no.startswith("P")
        assert transaction_no.startswith("T")
        return self.order


def build_client(
    auth_repo: FakeAuthRepository,
    order_repo: FakePaymentRepository,
    *,
    raise_server_exceptions: bool = True,
) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repo
    app.dependency_overrides[get_order_repository] = lambda: order_repo
    client = TestClient(app, raise_server_exceptions=raise_server_exceptions)
    client.cookies.set("scenic_session", auth_repo.session_token)
    client.cookies.set("scenic_csrf", auth_repo.csrf_token)
    return client


def csrf_headers(client: TestClient) -> dict[str, str]:
    token = client.cookies.get("scenic_csrf")
    assert token
    return {"x-csrf-token": token}


def registered_visitor(visitor_id: int = 1) -> VisitorRecord:
    return VisitorRecord(
        id=visitor_id,
        visitor_name="张三",
        id_type="ID_CARD",
        id_number="11010519491231002X",
        phone="13911112222",
        visitor_scope="REGISTERED",
    )


def test_pay_requires_idempotency_key():
    order_repo = FakePaymentRepository(visitor_id=1)
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)

    response = client.post("/api/orders/O202607010900000001/pay", headers=csrf_headers(client))

    assert response.status_code == 400
    assert response.json()["code"] == "IDEMPOTENCY_KEY_REQUIRED"


def test_pay_rejects_overlong_idempotency_key_before_database_work():
    order_repo = FakePaymentRepository(visitor_id=1)
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)

    response = client.post(
        "/api/orders/O202607010900000001/pay",
        headers=csrf_headers(client) | {"Idempotency-Key": "x" * 129},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "IDEMPOTENCY_KEY_INVALID"
    assert order_repo.quota_sold == 0


def test_pay_requires_csrf():
    order_repo = FakePaymentRepository(visitor_id=1)
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)

    response = client.post(
        "/api/orders/O202607010900000001/pay",
        headers={"Idempotency-Key": "pay-no-csrf"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_INVALID"


def test_pay_rejects_csrf_token_not_bound_to_session():
    order_repo = FakePaymentRepository(visitor_id=1)
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)
    client.cookies.set("scenic_csrf", "rotated-csrf")

    response = client.post(
        "/api/orders/O202607010900000001/pay",
        headers={
            "x-csrf-token": "rotated-csrf",
            "Idempotency-Key": "pay-rotated-csrf",
        },
    )

    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_INVALID"
    assert order_repo.quota_sold == 0


def test_repeated_same_idempotency_key_does_not_deduct_inventory_twice():
    order_repo = FakePaymentRepository(visitor_id=1)
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)
    headers = csrf_headers(client) | {"Idempotency-Key": "pay-once"}

    first = client.post("/api/orders/O202607010900000001/pay", headers=headers)
    second = client.post("/api/orders/O202607010900000001/pay", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert order_repo.quota_sold == 2
    assert first.json()["data"]["items"][0]["ticketCode"] == second.json()["data"]["items"][0]["ticketCode"]


def test_repeated_click_with_new_key_does_not_issue_new_tickets():
    order_repo = FakePaymentRepository(visitor_id=1)
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)
    headers = csrf_headers(client)

    first = client.post("/api/orders/O202607010900000001/pay", headers=headers | {"Idempotency-Key": "pay-1"})
    second = client.post("/api/orders/O202607010900000001/pay", headers=headers | {"Idempotency-Key": "pay-2"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert order_repo.quota_sold == 2
    assert first.json()["data"]["items"][1]["ticketCode"] == second.json()["data"]["items"][1]["ticketCode"]


def test_payment_returns_conflict_when_inventory_is_not_enough():
    order_repo = FakePaymentRepository(visitor_id=1, quota_remaining=1)
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)

    response = client.post(
        "/api/orders/O202607010900000001/pay",
        headers=csrf_headers(client) | {"Idempotency-Key": "pay-low-stock"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "TIME_SLOT_QUOTA_NOT_ENOUGH"
    assert order_repo.quota_sold == 0


def test_payment_for_another_visitor_order_returns_not_found():
    order_repo = FakePaymentRepository(visitor_id=2)
    client = build_client(FakeAuthRepository(registered_visitor(visitor_id=1)), order_repo)

    response = client.post(
        "/api/orders/O202607010900000001/pay",
        headers=csrf_headers(client) | {
            "Idempotency-Key": "pay-other",
            "x-request-id": "req-pay-other-order",
        },
    )

    data = response.json()
    assert response.status_code == 404
    assert data == {
        "success": False,
        "code": "ORDER_NOT_FOUND",
        "message": "订单不存在或无权限访问",
        "request_id": "req-pay-other-order",
    }
    assert response.headers["x-request-id"] == "req-pay-other-order"
    assert "O202607010900000001" not in str(data)


def test_cancelled_order_payment_returns_not_payable_without_inventory_change():
    order_repo = FakePaymentRepository(visitor_id=1)
    order_repo.order = OrderRecord(
        order_id=order_repo.order.order_id,
        order_no=order_repo.order.order_no,
        visitor_id=order_repo.order.visitor_id,
        buyer_name=order_repo.order.buyer_name,
        buyer_phone=order_repo.order.buyer_phone,
        order_status="CANCELLED",
        payment_status="UNPAID",
        total_amount=order_repo.order.total_amount,
        payable_amount=order_repo.order.payable_amount,
        order_time=order_repo.order.order_time,
        items=order_repo.order.items,
    )
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)

    response = client.post(
        "/api/orders/O202607010900000001/pay",
        headers=csrf_headers(client) | {"Idempotency-Key": "pay-cancelled"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "ORDER_NOT_PAYABLE"
    assert order_repo.quota_sold == 0
    assert order_repo.order.order_status == "CANCELLED"
    assert order_repo.order.items[0].ticket_code is None


def test_expired_unpaid_order_payment_returns_not_payable_and_cancels_items():
    order_repo = FakePaymentRepository(visitor_id=1, expire_on_call=True)
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)

    response = client.post(
        "/api/orders/O202607010900000001/pay",
        headers=csrf_headers(client) | {"Idempotency-Key": "pay-expired"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "ORDER_NOT_PAYABLE"
    assert order_repo.quota_sold == 0
    assert order_repo.order.order_status == "CANCELLED"
    assert order_repo.order.items[0].item_status == "CANCELLED"
    assert order_repo.order.items[0].ticket_code is None


def test_failed_payment_status_order_returns_not_payable_without_inventory_change():
    order_repo = FakePaymentRepository(visitor_id=1)
    order_repo.order = OrderRecord(
        order_id=order_repo.order.order_id,
        order_no=order_repo.order.order_no,
        visitor_id=order_repo.order.visitor_id,
        buyer_name=order_repo.order.buyer_name,
        buyer_phone=order_repo.order.buyer_phone,
        order_status="CREATED",
        payment_status="FAILED",
        total_amount=order_repo.order.total_amount,
        payable_amount=order_repo.order.payable_amount,
        order_time=order_repo.order.order_time,
        items=order_repo.order.items,
    )
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)

    response = client.post(
        "/api/orders/O202607010900000001/pay",
        headers=csrf_headers(client) | {"Idempotency-Key": "pay-failed-status"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "ORDER_NOT_PAYABLE"
    assert order_repo.quota_sold == 0
    assert order_repo.order.payment_status == "FAILED"
    assert order_repo.order.items[0].ticket_code is None


def test_ticket_codes_are_random_and_not_simple_sequence_values():
    order_repo = FakePaymentRepository(visitor_id=1)
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)

    response = client.post(
        "/api/orders/O202607010900000001/pay",
        headers=csrf_headers(client) | {"Idempotency-Key": "pay-random"},
    )

    codes = [item["ticketCode"] for item in response.json()["data"]["items"]]
    assert response.status_code == 200
    assert len(set(codes)) == len(codes)
    assert all(code.startswith("TK") for code in codes)
    assert all(not code.removeprefix("TK").isdigit() for code in codes)


def test_payment_failure_rolls_back_fake_inventory_and_order_state():
    order_repo = FakePaymentRepository(visitor_id=1, fail_after_stock=True)
    client = build_client(FakeAuthRepository(registered_visitor()), order_repo)

    response = client.post(
        "/api/orders/O202607010900000001/pay",
        headers=csrf_headers(client) | {"Idempotency-Key": "pay-fail"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "ORDER_NOT_PAYABLE"
    assert order_repo.quota_sold == 0
    assert order_repo.order.order_status == "CREATED"
    assert order_repo.order.items[0].ticket_code is None


def test_payment_unhandled_error_returns_generic_contract_without_sensitive_detail():
    sensitive_error = (
        "INSERT INTO payment_record failed for order_no=O202607010900000001 "
        "idempotency_key=pay-sensitive-key"
    )
    order_repo = FakePaymentRepository(visitor_id=1, unhandled_error_text=sensitive_error)
    client = build_client(
        FakeAuthRepository(registered_visitor()),
        order_repo,
        raise_server_exceptions=False,
    )

    response = client.post(
        "/api/orders/O202607010900000001/pay",
        headers=csrf_headers(client) | {
            "Idempotency-Key": "pay-sensitive-key",
            "x-request-id": "req-pay-unhandled",
        },
    )

    data = response.json()
    assert response.status_code == 500
    assert data == {
        "success": False,
        "code": "INTERNAL_SERVER_ERROR",
        "message": "服务暂时不可用",
        "request_id": "req-pay-unhandled",
    }
    assert response.headers["x-request-id"] == "req-pay-unhandled"
    response_text = response.text.lower()
    for leaked_text in (
        "insert",
        "payment_record",
        "order_no",
        "o202607010900000001",
        "idempotency",
        "pay-sensitive-key",
    ):
        assert leaked_text not in response_text


class ScriptedCursor:
    def __init__(self, result):
        self.result = result

    def fetchone(self):
        return self.result

    def fetchall(self):
        return self.result


class ScriptedConnection:
    def __init__(self, results: list, fail_on_query_part: str | None = None):
        self.results = results
        self.fail_on_query_part = fail_on_query_part
        self.queries: list[str] = []
        self.executions: list[tuple[str, tuple | None]] = []
        self.saw_exception = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_exc_info):
        self.saw_exception = exc_type is not None
        return False

    def execute(self, query: str, params: tuple | None = None):
        self.queries.append(query)
        self.executions.append((query, params))
        if self.fail_on_query_part and self.fail_on_query_part in query:
            raise RuntimeError("simulated database failure")
        return ScriptedCursor(self.results.pop(0))


def test_postgres_payment_uses_single_transaction_and_locks_order(monkeypatch):
    order_row = {
        "order_id": 1,
        "order_no": "O202607010900000001",
        "visitor_id": 1,
        "buyer_name": "张三",
        "buyer_phone": "13911112222",
        "order_status": "CREATED",
        "payment_status": "UNPAID",
        "total_amount": Decimal("128.00"),
        "payable_amount": Decimal("128.00"),
        "order_time": datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
    }
    item_row = {
        "order_item_id": 9,
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
        "item_status": "PENDING_PAYMENT",
        "ticket_code": None,
    }
    paid_item_row = item_row | {"item_status": "UNUSED", "ticket_code": "TKRANDOMABC123"}
    connection = ScriptedConnection(
        results=[
            order_row,
            None,
            [item_row],
            {"id": 100},
            None,
            None,
            None,
            order_row | {"order_status": "PAID", "payment_status": "PAID"},
            [paid_item_row],
        ]
    )
    monkeypatch.setattr(order_repository_module, "connect_db", lambda: connection)

    order = PostgresOrderRepository().pay_order(
        order_no="O202607010900000001",
        visitor_id=1,
        idempotency_key="pay-key",
        payment_no="P001",
        transaction_no="T001",
        ticket_code_factory=lambda: "TKRANDOMABC123",
    )

    queries = "\n".join(connection.queries)
    assert order.order_status == "PAID"
    assert "FOR UPDATE" in connection.queries[0]
    assert "WHERE order_no = %s AND visitor_id = %s" in connection.queries[0]
    assert "WHERE order_id = %s AND idempotency_key = %s" in queries
    assert connection.executions[0][1] == ("O202607010900000001", 1)
    assert connection.executions[1][1] == (1, "pay-key")
    assert "UPDATE time_slot_quota" in queries
    assert "quota_sold + %s <= quota_total" in queries
    assert "JOIN route_product rp ON rp.id = toi.product_id" in queries
    assert "INSERT INTO payment_record" in queries
    assert "ticket_code = %s" in queries


def test_postgres_payment_rejects_cancelled_order_before_inventory_and_ticket_updates(monkeypatch):
    cancelled_order_row = {
        "order_id": 1,
        "order_no": "O202607010900000001",
        "visitor_id": 1,
        "buyer_name": "张三",
        "buyer_phone": "13911112222",
        "order_status": "CANCELLED",
        "payment_status": "UNPAID",
        "total_amount": Decimal("128.00"),
        "payable_amount": Decimal("128.00"),
        "order_time": datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
    }
    connection = ScriptedConnection(results=[cancelled_order_row, None])
    monkeypatch.setattr(order_repository_module, "connect_db", lambda: connection)

    with pytest.raises(OrderPaymentStateError):
        PostgresOrderRepository().pay_order(
            order_no="O202607010900000001",
            visitor_id=1,
            idempotency_key="pay-cancelled",
            payment_no="P001",
            transaction_no="T001",
            ticket_code_factory=lambda: "TKRANDOMABC123",
        )

    queries = "\n".join(connection.queries)
    assert "WHERE order_no = %s AND visitor_id = %s" in connection.queries[0]
    assert "WHERE order_id = %s AND idempotency_key = %s" in queries
    assert "UPDATE time_slot_quota" not in queries
    assert "INSERT INTO payment_record" not in queries
    assert "UPDATE ticket_order_item" not in queries
    assert "UPDATE ticket_order" not in queries


def test_postgres_payment_rejects_failed_payment_status_before_inventory_and_ticket_updates(monkeypatch):
    failed_payment_order_row = {
        "order_id": 1,
        "order_no": "O202607010900000001",
        "visitor_id": 1,
        "buyer_name": "张三",
        "buyer_phone": "13911112222",
        "order_status": "CREATED",
        "payment_status": "FAILED",
        "total_amount": Decimal("128.00"),
        "payable_amount": Decimal("128.00"),
        "order_time": datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
    }
    connection = ScriptedConnection(results=[failed_payment_order_row, None])
    monkeypatch.setattr(order_repository_module, "connect_db", lambda: connection)

    with pytest.raises(OrderPaymentStateError):
        PostgresOrderRepository().pay_order(
            order_no="O202607010900000001",
            visitor_id=1,
            idempotency_key="pay-failed-status",
            payment_no="P001",
            transaction_no="T001",
            ticket_code_factory=lambda: "TKRANDOMABC123",
        )

    queries = "\n".join(connection.queries)
    assert "WHERE order_no = %s AND visitor_id = %s" in connection.queries[0]
    assert "WHERE order_id = %s AND idempotency_key = %s" in queries
    assert "UPDATE time_slot_quota" not in queries
    assert "INSERT INTO payment_record" not in queries
    assert "UPDATE ticket_order_item" not in queries
    assert "UPDATE ticket_order" not in queries


def test_postgres_payment_stops_before_payment_and_ticket_updates_when_quota_is_not_enough(monkeypatch):
    order_row = {
        "order_id": 1,
        "order_no": "O202607010900000001",
        "visitor_id": 1,
        "buyer_name": "张三",
        "buyer_phone": "13911112222",
        "order_status": "CREATED",
        "payment_status": "UNPAID",
        "total_amount": Decimal("128.00"),
        "payable_amount": Decimal("128.00"),
        "order_time": datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
    }
    item_row = {
        "order_item_id": 9,
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
        "item_status": "PENDING_PAYMENT",
        "ticket_code": None,
    }
    connection = ScriptedConnection(results=[order_row, None, [item_row], None])
    monkeypatch.setattr(order_repository_module, "connect_db", lambda: connection)

    with pytest.raises(OrderQuotaNotEnoughError):
        PostgresOrderRepository().pay_order(
            order_no="O202607010900000001",
            visitor_id=1,
            idempotency_key="pay-low-stock",
            payment_no="P001",
            transaction_no="T001",
            ticket_code_factory=lambda: "TKRANDOMABC123",
        )

    queries = "\n".join(connection.queries)
    assert connection.saw_exception is True
    assert "UPDATE time_slot_quota" in queries
    assert "quota_sold + %s <= quota_total" in queries
    assert "INSERT INTO payment_record" not in queries
    assert "UPDATE ticket_order_item" not in queries
    assert "UPDATE ticket_order" not in queries


def test_postgres_payment_exception_leaves_transaction_to_connection_rollback(monkeypatch):
    order_row = {
        "order_id": 1,
        "order_no": "O202607010900000001",
        "visitor_id": 1,
        "buyer_name": "张三",
        "buyer_phone": "13911112222",
        "order_status": "CREATED",
        "payment_status": "UNPAID",
        "total_amount": Decimal("128.00"),
        "payable_amount": Decimal("128.00"),
        "order_time": datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
    }
    item_row = {
        "order_item_id": 9,
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
        "item_status": "PENDING_PAYMENT",
        "ticket_code": None,
    }
    connection = ScriptedConnection(
        results=[order_row, None, [item_row], {"id": 100}],
        fail_on_query_part="INSERT INTO payment_record",
    )
    monkeypatch.setattr(order_repository_module, "connect_db", lambda: connection)

    with pytest.raises(RuntimeError, match="simulated database failure"):
        PostgresOrderRepository().pay_order(
            order_no="O202607010900000001",
            visitor_id=1,
            idempotency_key="pay-key",
            payment_no="P001",
            transaction_no="T001",
            ticket_code_factory=lambda: "TKRANDOMABC123",
        )

    queries = "\n".join(connection.queries)
    assert connection.saw_exception is True
    assert any("UPDATE time_slot_quota" in query for query in connection.queries)
    assert "INSERT INTO payment_record" in queries
    assert "UPDATE ticket_order_item" not in queries
    assert "UPDATE ticket_order" not in queries
