import json
from datetime import UTC, date, datetime, time
from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import create_app
from app.repositories.auth import SessionVisitorRecord, VisitorConflictError, VisitorRecord, get_auth_repository
from app.repositories.catalog import ProductRecord, TimeSlotRecord, get_catalog_repository
from app.repositories.orders import (
    OrderCancelStateError,
    OrderCreateItemRecord,
    OrderPaymentStateError,
    OrderQuotaNotEnoughError,
    OrderQuoteRecord,
    OrderRecord,
    PendingOrderItemInput,
    get_order_repository,
)

SENSITIVE_RESPONSE_KEYS = {
    "accessToken",
    "csrf",
    "csrf_token",
    "csrfToken",
    "csrfTokenHash",
    "idNumber",
    "idType",
    "passwordHash",
    "refreshToken",
    "session",
    "sessionId",
    "sessionToken",
    "sessionTokenHash",
    "visitorId",
}
SENSITIVE_RESPONSE_VALUES = {"11010519491231002X", "13911112222"}


class FlowAuthRepository:
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
        self.sessions[session_token_hash] = SessionVisitorRecord(
            session_id=self.next_session_id,
            visitor=self.visitors[visitor_id],
            csrf_token_hash=csrf_token_hash,
            expires_at=expires_at,
            revoked_at=None,
        )
        self.next_session_id += 1
        assert csrf_token_hash

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

    def touch_session(self, _session_id: int) -> None:
        pass


class FlowCatalogRepository:
    def __init__(self):
        self.product = ProductRecord(
            product_id=1,
            ticket_type_id=10,
            scenic_spot_name="遇龙河景区",
            product_name="金龙桥至旧县成人票",
            ticket_name="遇龙河成人票",
            ticket_category="ADULT",
            original_price=Decimal("168.00"),
            sale_price=Decimal("128.00"),
            description="成人竹筏漂流票",
            refund_rule="游玩日前一天18:00前可退",
            real_name_required=True,
            trip_type="ONE_WAY",
            raft_capacity=2,
            start_pier_name="金龙桥码头",
            end_pier_name="旧县码头",
            window_phone="0773-1234567",
        )
        self.slot = TimeSlotRecord(
            time_slot_id=100,
            product_id=1,
            ticket_type_id=10,
            visit_date=date(2026, 7, 1),
            slot_start_time=time(8, 30),
            slot_end_time=time(10, 30),
            quota_remaining=5,
        )

    def list_products(self) -> list[ProductRecord]:
        return [self.product]

    def list_time_slots(
        self,
        visit_date: date | None = None,
        ticket_type_id: int | None = None,
        product_id: int | None = None,
    ) -> list[TimeSlotRecord]:
        slots = [self.slot]
        if visit_date is not None:
            slots = [slot for slot in slots if slot.visit_date == visit_date]
        if ticket_type_id is not None:
            slots = [slot for slot in slots if slot.ticket_type_id == ticket_type_id]
        if product_id is not None:
            slots = [slot for slot in slots if slot.product_id == product_id]
        return slots


class FlowOrderRepository:
    def __init__(self):
        self.next_order_id = 1
        self.quota_sold = 0
        self.orders: dict[str, OrderRecord] = {}
        self.payments: set[tuple[str, str]] = set()

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
        assert scenic_spot_id == 1
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

    def pay_order(
        self,
        order_no: str,
        visitor_id: int,
        idempotency_key: str,
        payment_no: str,
        transaction_no: str,
        ticket_code_factory,
    ) -> OrderRecord | None:
        order = self.get_order_for_visitor(visitor_id, order_no)
        if order is None:
            return None
        payment_key = (order_no, idempotency_key)
        if payment_key in self.payments or order.order_status == "PAID":
            return order
        if order.order_status != "CREATED" or order.payment_status != "UNPAID":
            raise OrderPaymentStateError
        if 5 - self.quota_sold < len(order.items):
            raise OrderQuotaNotEnoughError

        self.quota_sold += len(order.items)
        paid_items = [
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
                item_status="UNUSED",
                ticket_code=ticket_code_factory(),
                passenger_name=item.passenger_name,
                passenger_id_type=item.passenger_id_type,
                passenger_id_number=item.passenger_id_number,
                passenger_phone=item.passenger_phone,
            )
            for item in order.items
        ]
        paid_order = OrderRecord(
            order_id=order.order_id,
            order_no=order.order_no,
            visitor_id=order.visitor_id,
            buyer_name=order.buyer_name,
            buyer_phone=order.buyer_phone,
            order_status="PAID",
            payment_status="PAID",
            total_amount=order.total_amount,
            payable_amount=order.payable_amount,
            order_time=order.order_time,
            items=paid_items,
        )
        self.orders[order_no] = paid_order
        self.payments.add(payment_key)
        assert payment_no.startswith("P")
        assert transaction_no.startswith("T")
        return paid_order

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
                item_status="CANCELLED" if item.item_status == "PENDING_PAYMENT" else item.item_status,
                ticket_code=item.ticket_code,
                passenger_name=item.passenger_name,
                passenger_id_type=item.passenger_id_type,
                passenger_id_number=item.passenger_id_number,
                passenger_phone=item.passenger_phone,
            )
            for item in order.items
        ]
        cancelled_order = OrderRecord(
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
        self.orders[order_no] = cancelled_order
        return cancelled_order


def build_client() -> tuple[TestClient, FlowOrderRepository]:
    auth_repo = FlowAuthRepository()
    catalog_repo = FlowCatalogRepository()
    order_repo = FlowOrderRepository()
    app = create_app()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repo
    app.dependency_overrides[get_catalog_repository] = lambda: catalog_repo
    app.dependency_overrides[get_order_repository] = lambda: order_repo
    return TestClient(app), order_repo


def csrf_headers(client: TestClient) -> dict[str, str]:
    response = client.get("/api/auth/csrf")
    assert response.status_code == 200
    token = client.cookies.get("scenic_csrf")
    assert token
    return {"x-csrf-token": token}


def assert_no_sensitive_response_fields(payload) -> None:
    serialized_payload = json.dumps(payload, ensure_ascii=False, default=str)
    for sensitive_value in SENSITIVE_RESPONSE_VALUES:
        assert sensitive_value not in serialized_payload

    if isinstance(payload, dict):
        for key, value in payload.items():
            assert key not in SENSITIVE_RESPONSE_KEYS
            assert_no_sensitive_response_fields(value)
    elif isinstance(payload, list):
        for item in payload:
            assert_no_sensitive_response_fields(item)


def test_registered_visitor_can_complete_ticket_purchase_flow():
    client, order_repo = build_client()
    headers = csrf_headers(client)

    register_response = client.post(
        "/api/auth/visitor/register",
        json={
            "username": "zhangsan_001",
            "password": "Visitor123",
            "phone": "13911112222",
        },
        headers=headers,
    )
    me_response = client.get("/api/auth/me")
    products_response = client.get("/api/catalog/products")
    slots_response = client.get(
        "/api/catalog/time-slots",
        params={"visitDate": "2026-07-01", "ticketTypeId": 10, "productId": 1},
    )
    create_response = client.post("/api/orders", json=order_payload(), headers=headers)

    assert register_response.status_code == 200
    assert me_response.json()["data"]["isRegistered"] is True

    assert products_response.status_code == 200
    assert products_response.json()["data"][0]["productId"] == 1
    assert slots_response.status_code == 200
    assert slots_response.json()["data"][0]["quotaRemaining"] == 5

    assert create_response.status_code == 200
    created_order = create_response.json()["data"]
    assert created_order["orderStatus"] == "CREATED"
    assert created_order["paymentStatus"] == "UNPAID"
    assert created_order["buyerPhone"] == "139****2222"
    assert "visitorId" not in created_order

    order_no = created_order["orderNo"]
    pay_response = client.post(
        f"/api/orders/{order_no}/pay",
        headers=headers | {"Idempotency-Key": "visitor-flow-pay"},
    )
    list_response = client.get("/api/me/orders?status=PAID")
    detail_response = client.get(f"/api/me/orders/{order_no}")
    cancel_paid_response = client.post(f"/api/orders/{order_no}/cancel", headers=headers)

    assert pay_response.status_code == 200
    paid_order = pay_response.json()["data"]
    assert paid_order["orderStatus"] == "PAID"
    assert paid_order["paymentStatus"] == "PAID"
    assert paid_order["items"][0]["ticketCode"].startswith("TK")
    assert order_repo.quota_sold == 2

    assert list_response.status_code == 200
    assert [order["orderNo"] for order in list_response.json()["data"]] == [order_no]
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["items"][0]["slotStartTime"] == "08:30:00"
    assert cancel_paid_response.status_code == 409
    assert cancel_paid_response.json()["code"] == "ORDER_NOT_CANCELABLE"

    public_response_payloads = [
        products_response.json()["data"],
        slots_response.json()["data"],
        created_order,
        paid_order,
        list_response.json()["data"],
        detail_response.json()["data"],
    ]
    for payload in public_response_payloads:
        assert_no_sensitive_response_fields(payload)


def test_inventory_payment_failure_keeps_pending_order_cancelable():
    client, order_repo = build_client()
    headers = csrf_headers(client)

    register_response = client.post(
        "/api/auth/visitor/register",
        json={
            "username": "zhangsan_001",
            "password": "Visitor123",
            "phone": "13911112222",
        },
        headers=headers,
    )
    create_response = client.post("/api/orders", json=order_payload(), headers=headers)
    order_no = create_response.json()["data"]["orderNo"]
    order_repo.quota_sold = 4

    pay_response = client.post(
        f"/api/orders/{order_no}/pay",
        headers=headers | {"Idempotency-Key": "visitor-flow-low-stock"},
    )
    detail_after_pay_failure_response = client.get(f"/api/me/orders/{order_no}")
    cancel_response = client.post(f"/api/orders/{order_no}/cancel", headers=headers)

    assert register_response.status_code == 200
    assert create_response.status_code == 200
    assert pay_response.status_code == 409
    assert pay_response.json()["code"] == "TIME_SLOT_QUOTA_NOT_ENOUGH"
    assert detail_after_pay_failure_response.status_code == 200
    pending_order = detail_after_pay_failure_response.json()["data"]
    assert pending_order["orderStatus"] == "CREATED"
    assert pending_order["paymentStatus"] == "UNPAID"
    assert all(item["itemStatus"] == "PENDING_PAYMENT" for item in pending_order["items"])
    assert all("ticketCode" not in item for item in pending_order["items"])

    assert cancel_response.status_code == 200
    cancelled_order = cancel_response.json()["data"]
    assert cancelled_order["orderStatus"] == "CANCELLED"
    assert cancelled_order["paymentStatus"] == "UNPAID"
    assert all(item["itemStatus"] == "CANCELLED" for item in cancelled_order["items"])
    assert order_repo.quota_sold == 4


def order_payload() -> dict:
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
