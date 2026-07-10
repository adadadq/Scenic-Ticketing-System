import hashlib
import hmac
import json
import time
from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient

import app.repositories.orders as order_repository_module
from app.core.config import SecuritySettings, get_settings
from app.main import create_app
from app.repositories.orders import (
    MockPaymentCallbackRecord,
    OrderPaymentAmountMismatchError,
    OrderPaymentStateError,
    OrderQuotaNotEnoughError,
    PostgresOrderRepository,
    get_order_repository,
)


class FakeMockPaymentCallbackRepository:
    def __init__(self):
        self.callback_count = 0
        self.quota_sold = 0
        self.order_status = "CREATED"
        self.payment_status = "UNPAID"
        self.payable_amount = Decimal("256.00")
        self.processed_events: set[str] = set()
        self.ticket_codes: list[str] = []
        self.order_missing = False
        self.quota_not_enough = False

    def process_mock_payment_callback(
        self,
        event_id: str,
        order_no: str,
        payment_no: str,
        transaction_no: str,
        paid_amount: Decimal,
        ticket_code_factory,
    ) -> MockPaymentCallbackRecord | None:
        if self.order_missing or order_no != "O202607010900000001":
            return None
        if event_id in self.processed_events:
            return self.record(event_id, idempotent=True)
        if paid_amount != self.payable_amount:
            raise OrderPaymentAmountMismatchError
        if self.order_status != "CREATED" or self.payment_status != "UNPAID":
            raise OrderPaymentStateError
        if self.quota_not_enough:
            raise OrderQuotaNotEnoughError

        self.callback_count += 1
        self.quota_sold += 2
        self.ticket_codes = [ticket_code_factory(), ticket_code_factory()]
        self.order_status = "PAID"
        self.payment_status = "PAID"
        self.processed_events.add(event_id)
        assert payment_no == "P202607010001"
        assert transaction_no == "T202607010001"
        return self.record(event_id, idempotent=False)

    def record(self, event_id: str, idempotent: bool) -> MockPaymentCallbackRecord:
        return MockPaymentCallbackRecord(
            event_id=event_id,
            order_no="O202607010900000001",
            order_status=self.order_status,
            payment_status=self.payment_status,
            idempotent=idempotent,
            processed_at=datetime(2026, 7, 1, 9, 30, tzinfo=UTC),
        )


def build_client(repository: FakeMockPaymentCallbackRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_order_repository] = lambda: repository
    return TestClient(app)


def callback_payload(**overrides) -> dict:
    payload = {
        "eventId": "evt_202607010001",
        "orderNo": "O202607010900000001",
        "paymentNo": "P202607010001",
        "transactionNo": "T202607010001",
        "paidAmount": "256.00",
        "paymentStatus": "SUCCESS",
    }
    payload.update(overrides)
    return payload


def raw_json(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def signed_headers(raw_body: bytes, timestamp: int | None = None, secret: str | None = None) -> dict[str, str]:
    timestamp_text = str(timestamp if timestamp is not None else int(time.time()))
    key = secret or SecuritySettings.mockpay_callback_secret
    signature = hmac.new(
        key.encode("utf-8"),
        timestamp_text.encode("utf-8") + b"." + raw_body,
        hashlib.sha256,
    ).hexdigest()
    return {
        "content-type": "application/json",
        "X-Mockpay-Timestamp": timestamp_text,
        "X-Mockpay-Signature": signature,
    }


def post_callback(client: TestClient, payload: dict, headers: dict[str, str] | None = None):
    body = raw_json(payload)
    return client.post(
        "/api/payments/mock/callback",
        content=body,
        headers=headers if headers is not None else signed_headers(body),
    )


def test_signed_mock_payment_callback_pays_order_without_session_or_csrf():
    repository = FakeMockPaymentCallbackRepository()
    client = build_client(repository)

    response = post_callback(client, callback_payload())

    assert response.status_code == 200
    assert response.json()["data"] == {
        "eventId": "evt_202607010001",
        "orderNo": "O202607010900000001",
        "orderStatus": "PAID",
        "paymentStatus": "PAID",
        "idempotent": False,
        "processedAt": "2026-07-01T09:30:00Z",
    }
    assert repository.callback_count == 1
    assert repository.quota_sold == 2
    assert len(repository.ticket_codes) == 2
    assert "session" not in response.text.lower()
    assert "csrf" not in response.text.lower()
    assert "password" not in response.text.lower()
    assert "hash" not in response.text.lower()


def test_mock_payment_callback_rejects_missing_bad_or_expired_signature_before_repository():
    repository = FakeMockPaymentCallbackRepository()
    client = build_client(repository)
    payload = callback_payload()
    body = raw_json(payload)

    missing = client.post("/api/payments/mock/callback", content=body, headers={"content-type": "application/json"})
    bad = client.post(
        "/api/payments/mock/callback",
        content=body,
        headers=signed_headers(body) | {"X-Mockpay-Signature": "0" * 64},
    )
    expired = client.post(
        "/api/payments/mock/callback",
        content=body,
        headers=signed_headers(body, timestamp=1),
    )

    assert missing.status_code == 401
    assert missing.json()["code"] == "MOCKPAY_SIGNATURE_INVALID"
    assert bad.status_code == 401
    assert bad.json()["code"] == "MOCKPAY_SIGNATURE_INVALID"
    assert expired.status_code == 401
    assert expired.json()["code"] == "MOCKPAY_TIMESTAMP_INVALID"
    assert repository.callback_count == 0
    assert repository.quota_sold == 0
    assert SecuritySettings.mockpay_callback_secret not in missing.text + bad.text + expired.text


def test_mock_payment_callback_verifies_signature_before_body_validation():
    repository = FakeMockPaymentCallbackRepository()
    client = build_client(repository)
    invalid_body = b'{"eventId":'

    bad_signature = client.post(
        "/api/payments/mock/callback",
        content=invalid_body,
        headers=signed_headers(invalid_body) | {"X-Mockpay-Signature": "bad-signature"},
    )
    valid_signature = client.post(
        "/api/payments/mock/callback",
        content=invalid_body,
        headers=signed_headers(invalid_body),
    )

    assert bad_signature.status_code == 401
    assert bad_signature.json()["code"] == "MOCKPAY_SIGNATURE_INVALID"
    assert valid_signature.status_code == 422
    assert valid_signature.json()["code"] == "VALIDATION_ERROR"
    assert repository.callback_count == 0


def test_mock_payment_callback_is_idempotent_for_repeated_event():
    repository = FakeMockPaymentCallbackRepository()
    client = build_client(repository)
    payload = callback_payload()

    first = post_callback(client, payload)
    second = post_callback(client, payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["idempotent"] is False
    assert second.json()["data"]["idempotent"] is True
    assert repository.callback_count == 1
    assert repository.quota_sold == 2
    assert first.json()["data"]["orderStatus"] == second.json()["data"]["orderStatus"] == "PAID"


def test_mock_payment_callback_rejects_new_event_for_already_paid_order_even_when_amount_differs():
    repository = FakeMockPaymentCallbackRepository()
    client = build_client(repository)

    first = post_callback(client, callback_payload())
    new_event_same_amount = post_callback(client, callback_payload(eventId="evt_new_paid"))
    new_event_bad_amount = post_callback(client, callback_payload(eventId="evt_new_paid_bad_amount", paidAmount="255.00"))

    assert first.status_code == 200
    assert new_event_same_amount.status_code == 409
    assert new_event_same_amount.json()["code"] == "ORDER_NOT_PAYABLE"
    assert new_event_bad_amount.status_code == 409
    assert new_event_bad_amount.json()["code"] == "MOCKPAY_AMOUNT_MISMATCH"
    assert repository.callback_count == 1
    assert repository.quota_sold == 2


def test_mock_payment_callback_maps_domain_errors():
    repository = FakeMockPaymentCallbackRepository()
    client = build_client(repository)

    invalid_event = post_callback(client, callback_payload(paymentStatus="FAILED"))
    mismatch = post_callback(client, callback_payload(eventId="evt_amount", paidAmount="255.00"))
    repository.order_missing = True
    missing = post_callback(client, callback_payload(eventId="evt_missing"))

    assert invalid_event.status_code == 422
    assert invalid_event.json()["code"] == "MOCKPAY_EVENT_INVALID"
    assert mismatch.status_code == 409
    assert mismatch.json()["code"] == "MOCKPAY_AMOUNT_MISMATCH"
    assert missing.status_code == 404
    assert missing.json()["code"] == "MOCKPAY_ORDER_NOT_FOUND"


def test_mock_payment_callback_maps_not_payable_and_quota_errors():
    repository = FakeMockPaymentCallbackRepository()
    client = build_client(repository)

    repository.order_status = "CANCELLED"
    not_payable = post_callback(client, callback_payload(eventId="evt_cancelled"))

    repository.order_status = "CREATED"
    repository.quota_not_enough = True
    low_stock = post_callback(client, callback_payload(eventId="evt_low_stock"))

    assert not_payable.status_code == 409
    assert not_payable.json()["code"] == "ORDER_NOT_PAYABLE"
    assert low_stock.status_code == 409
    assert low_stock.json()["code"] == "TIME_SLOT_QUOTA_NOT_ENOUGH"
    assert repository.callback_count == 0
    assert repository.quota_sold == 0


def test_postgres_mock_payment_callback_locks_order_items_and_uses_event_idempotency(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            sql = calls[-1][0]
            if "FROM payment_record pr" in sql:
                return None
            if "FROM ticket_order\n" in sql:
                return {
                    "order_id": 1,
                    "visitor_id": 7,
                    "order_no": "O202607010900000001",
                    "order_status": "CREATED",
                    "payment_status": "UNPAID",
                    "order_time": datetime.now(UTC),
                    "payable_amount": Decimal("256.00"),
                }
            if "FROM payment_record" in sql:
                return None
            if "UPDATE time_slot_quota" in sql:
                return {"id": 100}
            if "UPDATE ticket_order_item" in sql:
                return {"id": 10}
            return None

        def fetchall(self):
            return [
                {"order_item_id": 10, "item_status": "PENDING_PAYMENT", "time_slot_id": 100},
                {"order_item_id": 11, "item_status": "PENDING_PAYMENT", "time_slot_id": 100},
            ]

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    result = PostgresOrderRepository().process_mock_payment_callback(
        event_id="evt_202607010001",
        order_no="O202607010900000001",
        payment_no="P202607010001",
        transaction_no="T202607010001",
        paid_amount=Decimal("256.00"),
        ticket_code_factory=lambda: "TKCALLBACK001",
    )

    assert result is not None
    assert result.idempotent is False
    assert len(calls) == 9
    assert "FROM payment_record pr" in calls[0][0]
    assert calls[0][1] == ("mockpay:evt_202607010001",)
    assert "FOR UPDATE" in calls[1][0]
    assert calls[1][1] == ("O202607010900000001",)
    assert "payment_no = %s" in calls[2][0]
    assert calls[2][1] == ("P202607010001",)
    assert "FROM ticket_order_item" in calls[3][0]
    assert "FOR UPDATE" in calls[3][0]
    assert "UPDATE time_slot_quota" in calls[4][0]
    assert "quota_sold + %s <= quota_total" in calls[4][0]
    assert "INSERT INTO payment_record" in calls[5][0]
    assert calls[5][1][2] == "mockpay:evt_202607010001"
    assert "UPDATE ticket_order_item" in calls[6][0]
    assert "UPDATE ticket_order_item" in calls[7][0]
    assert "UPDATE ticket_order" in calls[8][0]


def test_postgres_mock_payment_callback_returns_idempotent_before_side_effects(monkeypatch):
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeCursor:
        def execute(self, sql: str, params: tuple[object, ...]):
            calls.append((sql, params))
            return self

        def fetchone(self):
            if "FROM payment_record pr" in calls[-1][0]:
                return {
                    "order_no": "O202607010900000001",
                    "order_status": "PAID",
                    "payment_status": "PAID",
                }
            return None

    class FakeConnection:
        def __enter__(self):
            return FakeCursor()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(order_repository_module, "connect_db", lambda: FakeConnection())

    result = PostgresOrderRepository().process_mock_payment_callback(
        event_id="evt_202607010001",
        order_no="O202607010900000001",
        payment_no="P202607010001",
        transaction_no="T202607010001",
        paid_amount=Decimal("256.00"),
        ticket_code_factory=lambda: "TKCALLBACK001",
    )

    assert result is not None
    assert result.idempotent is True
    assert len(calls) == 1
    assert calls[0][1] == ("mockpay:evt_202607010001",)
    assert not any("UPDATE time_slot_quota" in sql for sql, _params in calls)
    assert not any("INSERT INTO payment_record" in sql for sql, _params in calls)
    assert not any("UPDATE ticket_order_item" in sql for sql, _params in calls)
