from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

import app.repositories.orders as order_repository_module
from app.core.security import hash_password, hash_secret
from app.main import create_app
from app.repositories.auth import SessionVisitorRecord, VisitorConflictError, VisitorRecord, get_auth_repository
from app.repositories.orders import (
    OrderCreateItemRecord,
    PendingOrderItemInput,
    OrderQuoteRecord,
    OrderRecord,
    PostgresOrderRepository,
    get_order_repository,
)


class FakeAuthRepository:
    def __init__(self):
        self.next_visitor_id = 1
        self.next_session_id = 1
        self.visitors: dict[int, VisitorRecord] = {}
        self.sessions: dict[str, SessionVisitorRecord] = {}

    def find_visitor_by_phone(self, phone: str) -> VisitorRecord | None:
        return next((visitor for visitor in self.visitors.values() if visitor.phone == phone), None)

    def find_visitor_by_username(self, username: str) -> VisitorRecord | None:
        return next((visitor for visitor in self.visitors.values() if visitor.username == username), None)

    def find_visitor_by_id_doc(self, id_type: str, id_number: str) -> VisitorRecord | None:
        return next(
            (
                visitor
                for visitor in self.visitors.values()
                if visitor.id_type == id_type and visitor.id_number == id_number
            ),
            None,
        )

    def create_temp_visitor(self, phone: str) -> VisitorRecord:
        if self.find_visitor_by_phone(phone):
            raise VisitorConflictError
        visitor = VisitorRecord(
            id=self.next_visitor_id,
            visitor_name=f"临时游客{phone[-4:]}",
            id_type="TEMP_PHONE",
            id_number=phone,
            phone=phone,
            visitor_scope="TEMP",
        )
        self.next_visitor_id += 1
        self.visitors[visitor.id] = visitor
        return visitor

    def get_or_create_temp_visitor(self, phone: str) -> VisitorRecord:
        return self.find_visitor_by_phone(phone) or self.create_temp_visitor(phone)

    def create_registered_visitor(self, visitor_name: str, id_type: str, id_number: str, phone: str) -> VisitorRecord:
        if self.find_visitor_by_phone(phone) or self.find_visitor_by_id_doc(id_type, id_number):
            raise VisitorConflictError
        visitor = VisitorRecord(
            id=self.next_visitor_id,
            visitor_name=visitor_name,
            id_type=id_type,
            id_number=id_number,
            phone=phone,
            visitor_scope="REGISTERED",
        )
        self.next_visitor_id += 1
        self.visitors[visitor.id] = visitor
        return visitor

    def update_registered_visitor(self, visitor_id: int, visitor_name: str, id_type: str, id_number: str, phone: str) -> VisitorRecord:
        visitor = VisitorRecord(
            id=visitor_id,
            visitor_name=visitor_name,
            id_type=id_type,
            id_number=id_number,
            phone=phone,
            visitor_scope="REGISTERED",
        )
        self.visitors[visitor.id] = visitor
        return visitor

    def create_registered_account(self, username: str, password_hash: str, phone: str) -> VisitorRecord:
        if self.find_visitor_by_username(username) or self.find_visitor_by_phone(phone):
            raise VisitorConflictError
        visitor = VisitorRecord(
            id=self.next_visitor_id,
            visitor_name=username,
            id_type="ACCOUNT",
            id_number=f"ACCOUNT:{username}",
            phone=phone,
            visitor_scope="REGISTERED",
            username=username,
            password_hash=password_hash,
        )
        self.next_visitor_id += 1
        self.visitors[visitor.id] = visitor
        return visitor

    def update_registered_account(self, visitor_id: int, username: str, password_hash: str, phone: str) -> VisitorRecord:
        visitor = VisitorRecord(
            id=visitor_id,
            visitor_name=username,
            id_type="ACCOUNT",
            id_number=f"ACCOUNT:{username}",
            phone=phone,
            visitor_scope="REGISTERED",
            username=username,
            password_hash=password_hash,
        )
        self.visitors[visitor.id] = visitor
        return visitor

    def create_session(self, visitor_id: int, session_token_hash: str, csrf_token_hash: str, expires_at: datetime) -> None:
        visitor = self.visitors[visitor_id]
        self.sessions[session_token_hash] = SessionVisitorRecord(
            session_id=self.next_session_id,
            visitor=visitor,
            csrf_token_hash=csrf_token_hash,
            expires_at=expires_at,
            revoked_at=None,
        )
        self.next_session_id += 1

    def find_session_visitor(self, session_token_hash: str, now: datetime) -> SessionVisitorRecord | None:
        session = self.sessions.get(session_token_hash)
        if session is None or session.revoked_at is not None or session.expires_at <= now:
            return None
        return session

    def revoke_session(self, session_token_hash: str) -> None:
        session = self.sessions.get(session_token_hash)
        if session:
            self.sessions[session_token_hash] = SessionVisitorRecord(
                session_id=session.session_id,
                visitor=session.visitor,
                csrf_token_hash=session.csrf_token_hash,
                expires_at=session.expires_at,
                revoked_at=datetime.now(UTC),
            )

    def update_session_csrf(self, session_token_hash: str, csrf_token_hash: str, now: datetime) -> None:
        session = self.sessions.get(session_token_hash)
        if session is None or session.revoked_at is not None or session.expires_at <= now:
            return
        self.sessions[session_token_hash] = SessionVisitorRecord(
            session_id=session.session_id,
            visitor=session.visitor,
            csrf_token_hash=csrf_token_hash,
            expires_at=session.expires_at,
            revoked_at=session.revoked_at,
        )

    def touch_session(self, session_id: int) -> None:
        pass


class FakeOrderRepository:
    def __init__(self):
        self.quota_sold = 2
        self.next_order_id = 1
        self.orders: dict[str, OrderRecord] = {}

    def get_order_quote(self, product_id: int, time_slot_id: int, visit_date: date) -> OrderQuoteRecord | None:
        if (product_id, time_slot_id, visit_date) != (1, 100, date(2026, 7, 1)):
            return None
        return OrderQuoteRecord(
            scenic_spot_id=1,
            product_id=1,
            ticket_type_id=10,
            product_name="金龙桥至旧县成人票",
            ticket_name="遇龙河成人票",
            time_slot_id=100,
            visit_date=date(2026, 7, 1),
            slot_start_time=time(8, 30),
            slot_end_time=time(10, 30),
            original_price=Decimal("168.00"),
            sale_price=Decimal("128.00"),
            quota_remaining=5 - self.quota_sold,
        )

    def create_pending_order(
        self,
        order_no: str,
        visitor_id: int,
        scenic_spot_id: int,
        buyer_name: str,
        buyer_phone: str,
        items: list[PendingOrderItemInput],
    ) -> OrderRecord:
        item_records = [
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
                item_status="PENDING_PAYMENT",
                passenger_name=item.passenger_name,
                passenger_id_type=item.passenger_id_type,
                passenger_id_number=item.passenger_id_number,
                passenger_phone=item.passenger_phone,
            )
            for item in items
        ]
        total_amount = sum((item.final_price for item in item_records), Decimal("0.00"))
        order = OrderRecord(
            order_id=self.next_order_id,
            order_no=order_no,
            visitor_id=visitor_id,
            buyer_name=buyer_name,
            buyer_phone=buyer_phone,
            order_status="CREATED",
            payment_status="UNPAID",
            total_amount=total_amount,
            payable_amount=total_amount,
            order_time=datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
            items=item_records,
        )
        self.next_order_id += 1
        self.orders[order_no] = order
        return order

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


def build_client(auth_repo: FakeAuthRepository, order_repo: FakeOrderRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repo
    app.dependency_overrides[get_order_repository] = lambda: order_repo
    return TestClient(app)


def csrf_headers(client: TestClient) -> dict[str, str]:
    response = client.get("/api/auth/csrf")
    assert response.status_code == 200
    token = client.cookies.get("scenic_csrf")
    assert token
    return {"x-csrf-token": token}


def login_temp(client: TestClient, phone: str = "13911112222") -> dict[str, str]:
    headers = csrf_headers(client)
    auth_repo = client.app.dependency_overrides[get_auth_repository]()
    visitor = auth_repo.create_temp_visitor(phone)
    auth_repo.create_session(
        visitor_id=visitor.id,
        session_token_hash=hash_secret("temp-session-token"),
        csrf_token_hash=hash_secret(headers["x-csrf-token"]),
        expires_at=datetime.now(UTC) + timedelta(seconds=60),
    )
    client.cookies.set("scenic_session", "temp-session-token")
    return headers


def login_registered(
    client: TestClient,
    phone: str = "13911112222",
    username: str = "zhangsan_001",
    id_number: str | None = None,
) -> dict[str, str]:
    headers = csrf_headers(client)
    account_username = username if id_number is None else f"visitor_{phone}"
    response = client.post(
        "/api/auth/visitor/register",
        json={
            "username": account_username,
            "password": "Visitor123",
            "phone": phone,
        },
        headers=headers,
    )
    assert response.status_code == 200
    return headers


def valid_order_payload() -> dict:
    return {
        "buyerName": "张三",
        "buyerPhone": "13911112222",
        "items": [
            {
                "productId": 1,
                "timeSlotId": 100,
                "visitDate": "2026-07-01",
                "quantity": 2,
                "passengers": [
                    {
                        "passengerName": "张三",
                        "idType": "ID_CARD",
                        "idNumber": "11010519491231002X",
                        "phone": "13911112222",
                    },
                    {
                        "passengerName": "李四",
                        "idType": "ID_CARD",
                        "idNumber": "110105194912310038",
                        "phone": "13811112222",
                    },
                ],
            }
        ],
    }


def test_unauthenticated_visitor_cannot_create_order():
    client = build_client(FakeAuthRepository(), FakeOrderRepository())

    response = client.post("/api/orders", json=valid_order_payload(), headers=csrf_headers(client))

    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"


def test_temp_visitor_cannot_create_order():
    client = build_client(FakeAuthRepository(), FakeOrderRepository())
    headers = login_temp(client)

    response = client.post("/api/orders", json=valid_order_payload(), headers=headers)

    assert response.status_code == 403
    assert response.json()["code"] == "ACCOUNT_REQUIRED"


def test_registered_visitor_creates_pending_order_without_deducting_inventory():
    order_repo = FakeOrderRepository()
    client = build_client(FakeAuthRepository(), order_repo)
    headers = login_registered(client)
    quota_sold_before = order_repo.quota_sold

    response = client.post("/api/orders", json=valid_order_payload(), headers=headers)

    data = response.json()["data"]
    assert response.status_code == 200
    assert data["orderStatus"] == "CREATED"
    assert data["paymentStatus"] == "UNPAID"
    assert data["totalAmount"] == "256.00"
    assert data["payableAmount"] == "256.00"
    assert len(data["items"]) == 2
    assert data["items"][0]["itemStatus"] == "PENDING_PAYMENT"
    assert order_repo.quota_sold == quota_sold_before


def test_create_order_accepts_refreshed_csrf_token_after_session_rebind():
    client = build_client(FakeAuthRepository(), FakeOrderRepository())
    login_registered(client)
    refreshed_headers = csrf_headers(client)

    response = client.post("/api/orders", json=valid_order_payload(), headers=refreshed_headers)

    assert response.status_code == 200
    assert response.json()["data"]["orderStatus"] == "CREATED"


def test_create_order_requires_csrf():
    client = build_client(FakeAuthRepository(), FakeOrderRepository())
    login_registered(client)

    response = client.post("/api/orders", json=valid_order_payload(), headers={})

    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_INVALID"


def test_create_order_rejects_csrf_token_not_bound_to_session():
    client = build_client(FakeAuthRepository(), FakeOrderRepository())
    login_registered(client)
    client.cookies.set("scenic_csrf", "rotated-csrf")

    response = client.post(
        "/api/orders",
        json=valid_order_payload(),
        headers={"x-csrf-token": "rotated-csrf"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_INVALID"


def test_duplicate_order_lines_are_checked_against_aggregated_quota():
    order_repo = FakeOrderRepository()
    client = build_client(FakeAuthRepository(), order_repo)
    headers = login_registered(client)
    payload = valid_order_payload()
    payload["items"].append(
        {
            "productId": 1,
            "timeSlotId": 100,
            "visitDate": "2026-07-01",
            "quantity": 2,
            "passengers": [
                {
                    "passengerName": "王五",
                    "idType": "ID_CARD",
                    "idNumber": "110105194912310046",
                    "phone": "13711112222",
                },
                {
                    "passengerName": "赵六",
                    "idType": "ID_CARD",
                    "idNumber": "110105194912310054",
                    "phone": "13611112222",
                },
            ],
        }
    )

    response = client.post("/api/orders", json=payload, headers=headers)

    assert response.status_code == 409
    assert response.json()["code"] == "TIME_SLOT_QUOTA_NOT_ENOUGH"


def test_request_body_cannot_assign_visitor_id():
    client = build_client(FakeAuthRepository(), FakeOrderRepository())
    headers = login_registered(client)
    payload = valid_order_payload() | {"visitorId": 999}

    response = client.post("/api/orders", json=payload, headers=headers)

    assert response.status_code == 422


def test_my_orders_and_detail_are_filtered_by_current_visitor():
    auth_repo = FakeAuthRepository()
    order_repo = FakeOrderRepository()
    client_a = build_client(auth_repo, order_repo)
    headers_a = login_registered(client_a, phone="13911112222", id_number="11010519491231002X")
    create_response = client_a.post("/api/orders", json=valid_order_payload(), headers=headers_a)
    order_no = create_response.json()["data"]["orderNo"]

    client_b = build_client(auth_repo, order_repo)
    login_registered(client_b, phone="13811112222", id_number="110105194912310038")

    list_response = client_b.get("/api/me/orders")
    detail_response = client_b.get(f"/api/me/orders/{order_no}")

    assert list_response.status_code == 200
    assert list_response.json()["data"] == []
    assert detail_response.status_code == 404
    assert detail_response.json()["code"] == "ORDER_NOT_FOUND"


def test_my_order_detail_returns_only_me_dto_fields():
    client = build_client(FakeAuthRepository(), FakeOrderRepository())
    headers = login_registered(client)
    create_response = client.post("/api/orders", json=valid_order_payload(), headers=headers)
    order_no = create_response.json()["data"]["orderNo"]

    response = client.get(f"/api/me/orders/{order_no}")

    data = response.json()["data"]
    assert response.status_code == 200
    assert data["orderNo"] == order_no
    assert "visitorId" not in data
    assert "createdAt" not in data
    assert "remark" not in data
    assert "ticketCode" not in data["items"][0]


def test_expired_session_cannot_list_orders():
    auth_repo = FakeAuthRepository()
    order_repo = FakeOrderRepository()
    visitor = auth_repo.create_registered_visitor("张三", "ID_CARD", "11010519491231002X", "13911112222")
    session_token = "expired-session-token"
    auth_repo.sessions[hash_secret(session_token)] = SessionVisitorRecord(
        session_id=1,
        visitor=visitor,
        csrf_token_hash=hash_secret("csrf-token"),
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
        revoked_at=None,
    )
    client = build_client(auth_repo, order_repo)
    client.cookies.set("scenic_session", session_token)

    response = client.get("/api/me/orders")

    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"


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


def test_postgres_create_pending_order_does_not_update_inventory(monkeypatch):
    order_row = {
        "order_id": 1,
        "order_no": "O202607010900000001",
        "visitor_id": 7,
        "buyer_name": "张三",
        "buyer_phone": "13911112222",
        "order_status": "CREATED",
        "payment_status": "UNPAID",
        "total_amount": Decimal("128.00"),
        "payable_amount": Decimal("128.00"),
        "order_time": datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
    }
    item_row = {
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
        "passenger_name": "张三",
        "passenger_id_type": "ID_CARD",
        "passenger_id_number": "11010519491231002X",
        "passenger_phone": "13911112222",
    }
    connection = ScriptedConnection(results=[order_row, {"id": 99}, item_row])
    monkeypatch.setattr(order_repository_module, "connect_db", lambda: connection)

    order = PostgresOrderRepository().create_pending_order(
        order_no="O202607010900000001",
        visitor_id=7,
        scenic_spot_id=1,
        buyer_name="张三",
        buyer_phone="13911112222",
        items=[
            PendingOrderItemInput(
                item_no="I001",
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
                passenger_name="张三",
                passenger_id_type="ID_CARD",
                passenger_id_number="11010519491231002X",
                passenger_phone="13911112222",
            )
        ],
    )

    queries = "\n".join(query for query, _params in connection.queries)
    assert order.order_status == "CREATED"
    assert order.payment_status == "UNPAID"
    assert order.items[0].item_status == "PENDING_PAYMENT"
    assert "INSERT INTO ticket_order" in queries
    assert "INSERT INTO visitor_passenger_template" in queries
    assert "INSERT INTO ticket_order_item" in queries
    assert "ticket_type_id,\n                            product_id,\n                            visitor_id" in connection.queries[2][0]
    assert "UPDATE time_slot_quota" not in queries
    item_insert_params = connection.queries[2][1]
    assert item_insert_params[2] == 1
    assert item_insert_params[5] == 99
    assert item_insert_params[6] == "张三"
    assert item_insert_params[12] == Decimal("168.00")
    assert item_insert_params[13] == Decimal("40.00")
    assert item_insert_params[14] == Decimal("128.00")


def test_postgres_order_detail_filters_by_visitor_id(monkeypatch):
    order_row = {
        "order_id": 1,
        "order_no": "O202607010900000001",
        "visitor_id": 7,
        "buyer_name": "张三",
        "buyer_phone": "13911112222",
        "order_status": "CREATED",
        "payment_status": "UNPAID",
        "total_amount": Decimal("128.00"),
        "payable_amount": Decimal("128.00"),
        "order_time": datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
    }
    connection = ScriptedConnection(results=[order_row, []])
    monkeypatch.setattr(order_repository_module, "connect_db", lambda: connection)

    order = PostgresOrderRepository().get_order_for_visitor(7, "O202607010900000001")

    first_query, first_params = connection.queries[0]
    assert order.order_no == "O202607010900000001"
    assert "WHERE visitor_id = %s AND order_no = %s" in first_query
    assert first_params == (7, "O202607010900000001")
