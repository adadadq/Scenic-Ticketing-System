from datetime import date, time
from decimal import Decimal

from fastapi.testclient import TestClient

import app.repositories.catalog as catalog_repository_module
from app.main import create_app
from app.repositories.catalog import PostgresCatalogRepository, ProductRecord, TimeSlotRecord, get_catalog_repository


SENSITIVE_EXCEPTION_TEXT = "select id_number from visitor where csrf='raw-token'"


class FakeCatalogRepository:
    def __init__(self):
        self.products = [
            ProductRecord(
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
            ),
            ProductRecord(
                product_id=2,
                ticket_type_id=20,
                scenic_spot_name="遇龙河景区",
                product_name="金龙桥至旧县儿童票",
                ticket_name="遇龙河儿童票",
                ticket_category="CHILD",
                original_price=Decimal("84.00"),
                sale_price=Decimal("68.00"),
                description="儿童竹筏漂流票",
                refund_rule="游玩日前一天18:00前可退",
                real_name_required=True,
                trip_type="ONE_WAY",
                raft_capacity=2,
                start_pier_name="金龙桥码头",
                end_pier_name="旧县码头",
                window_phone="0773-1234567",
            ),
        ]
        self.time_slots = [
            TimeSlotRecord(
                time_slot_id=100,
                product_id=1,
                ticket_type_id=10,
                visit_date=date(2026, 7, 1),
                slot_start_time=time(8, 30),
                slot_end_time=time(10, 30),
                quota_remaining=35,
            ),
            TimeSlotRecord(
                time_slot_id=101,
                product_id=1,
                ticket_type_id=10,
                visit_date=date(2026, 7, 2),
                slot_start_time=time(10, 30),
                slot_end_time=time(12, 30),
                quota_remaining=0,
            ),
            TimeSlotRecord(
                time_slot_id=200,
                product_id=2,
                ticket_type_id=20,
                visit_date=date(2026, 7, 1),
                slot_start_time=time(8, 30),
                slot_end_time=time(10, 30),
                quota_remaining=12,
            ),
        ]

    def list_products(self) -> list[ProductRecord]:
        return self.products

    def list_time_slots(
        self,
        visit_date: date | None = None,
        ticket_type_id: int | None = None,
        product_id: int | None = None,
    ) -> list[TimeSlotRecord]:
        slots = self.time_slots
        if visit_date is not None:
            slots = [slot for slot in slots if slot.visit_date == visit_date]
        if ticket_type_id is not None:
            slots = [slot for slot in slots if slot.ticket_type_id == ticket_type_id]
        if product_id is not None:
            slots = [slot for slot in slots if slot.product_id == product_id]
        return slots


class FailingCatalogRepository(FakeCatalogRepository):
    def __init__(self, *, fail_products: bool = False, fail_time_slots: bool = False):
        super().__init__()
        self.fail_products = fail_products
        self.fail_time_slots = fail_time_slots

    def list_products(self) -> list[ProductRecord]:
        if self.fail_products:
            raise RuntimeError(SENSITIVE_EXCEPTION_TEXT)
        return super().list_products()

    def list_time_slots(
        self,
        visit_date: date | None = None,
        ticket_type_id: int | None = None,
        product_id: int | None = None,
    ) -> list[TimeSlotRecord]:
        if self.fail_time_slots:
            raise RuntimeError(SENSITIVE_EXCEPTION_TEXT)
        return super().list_time_slots(
            visit_date=visit_date,
            ticket_type_id=ticket_type_id,
            product_id=product_id,
        )


def build_client(repo: FakeCatalogRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_catalog_repository] = lambda: repo
    return TestClient(app)


def test_products_are_public_and_do_not_require_login():
    client = build_client(FakeCatalogRepository())

    response = client.get("/api/catalog/products")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(response.json()["data"]) == 2


def test_products_return_public_dto_without_internal_fields():
    client = build_client(FakeCatalogRepository())

    response = client.get("/api/catalog/products")

    product = response.json()["data"][0]
    assert product == {
        "productId": 1,
        "ticketTypeId": 10,
        "scenicSpotName": "遇龙河景区",
        "productName": "金龙桥至旧县成人票",
        "ticketName": "遇龙河成人票",
        "ticketCategory": "ADULT",
        "originalPrice": "168.00",
        "salePrice": "128.00",
        "description": "成人竹筏漂流票",
        "refundRule": "游玩日前一天18:00前可退",
        "realNameRequired": True,
        "tripType": "ONE_WAY",
        "raftCapacity": 2,
        "startPierName": "金龙桥码头",
        "endPierName": "旧县码头",
        "windowPhone": "0773-1234567",
    }
    assert "status" not in product
    assert "createdAt" not in product
    assert "updatedAt" not in product
    assert "remark" not in product


def test_time_slots_are_public_and_calculate_remaining_quota():
    client = build_client(FakeCatalogRepository())

    response = client.get("/api/catalog/time-slots")

    assert response.status_code == 200
    assert response.json()["data"][0]["quotaRemaining"] == 35
    assert response.json()["data"][1]["quotaRemaining"] == 0


def test_time_slots_filter_by_visit_date_ticket_type_and_product():
    client = build_client(FakeCatalogRepository())

    response = client.get(
        "/api/catalog/time-slots",
        params={
            "visitDate": "2026-07-01",
            "ticketTypeId": "10",
            "productId": "1",
        },
    )

    data = response.json()["data"]
    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["timeSlotId"] == 100
    assert data[0]["visitDate"] == "2026-07-01"
    assert data[0]["slotStartTime"] == "08:30:00"
    assert data[0]["slotEndTime"] == "10:30:00"


def test_time_slots_public_dto_does_not_expose_inventory_strategy_fields():
    client = build_client(FakeCatalogRepository())

    response = client.get("/api/catalog/time-slots")

    slot = response.json()["data"][0]
    assert "quotaRemaining" in slot
    assert "quotaTotal" not in slot
    assert "quotaSold" not in slot
    assert "quotaCheckedIn" not in slot
    assert "status" not in slot


def test_products_repository_failure_returns_catalog_unavailable_without_sensitive_detail():
    client = build_client(FailingCatalogRepository(fail_products=True))

    response = client.get("/api/catalog/products", headers={"x-request-id": "catalog-products-fail"})

    assert response.status_code == 503
    assert response.headers["x-request-id"] == "catalog-products-fail"
    assert response.json() == {
        "success": False,
        "code": "CATALOG_UNAVAILABLE",
        "message": "票品接口暂不可用",
        "request_id": "catalog-products-fail",
    }
    assert "id_number" not in response.text
    assert "csrf" not in response.text.lower()
    assert "raw-token" not in response.text


def test_time_slots_repository_failure_returns_time_slots_unavailable_without_sensitive_detail():
    client = build_client(FailingCatalogRepository(fail_time_slots=True))

    response = client.get(
        "/api/catalog/time-slots",
        headers={"x-request-id": "catalog-slots-fail"},
        params={
            "visitDate": "2026-07-01",
            "ticketTypeId": "10",
            "productId": "1",
        },
    )

    assert response.status_code == 503
    assert response.headers["x-request-id"] == "catalog-slots-fail"
    assert response.json() == {
        "success": False,
        "code": "TIME_SLOTS_UNAVAILABLE",
        "message": "时段接口暂不可用",
        "request_id": "catalog-slots-fail",
    }
    assert "id_number" not in response.text
    assert "csrf" not in response.text.lower()
    assert "raw-token" not in response.text


class CapturingCursor:
    def __init__(self, rows: list[dict]):
        self.rows = rows

    def fetchall(self) -> list[dict]:
        return self.rows


class CapturingConnection:
    def __init__(self, rows: list[dict]):
        self.rows = rows
        self.queries: list[tuple[str, tuple[object, ...] | None]] = []

    def __enter__(self):
        return self

    def __exit__(self, *_exc_info):
        return False

    def execute(self, query: str, params: tuple[object, ...] | None = None) -> CapturingCursor:
        self.queries.append((query, params))
        return CapturingCursor(self.rows)


def test_catalog_repository_filters_disabled_products(monkeypatch):
    connection = CapturingConnection(rows=[])
    monkeypatch.setattr(catalog_repository_module, "connect_db", lambda: connection)

    products = PostgresCatalogRepository().list_products()

    query, params = connection.queries[0]
    assert products == []
    assert params is None

    for status_filter in [
        "rp.status = 'ENABLED'",
        "tt.status = 'ENABLED'",
        "ss.status = 'ENABLED'",
        "start_pier.status = 'ENABLED'",
        "end_pier.status = 'ENABLED'",
    ]:
        assert status_filter in query


def test_catalog_repository_filters_disabled_time_slot_dependencies(monkeypatch):
    connection = CapturingConnection(rows=[])
    monkeypatch.setattr(catalog_repository_module, "connect_db", lambda: connection)

    slots = PostgresCatalogRepository().list_time_slots(
        visit_date=date(2026, 7, 1),
        ticket_type_id=10,
        product_id=1,
    )

    query, params = connection.queries[0]
    assert slots == []
    assert params == (date(2026, 7, 1), 10, 1)

    for status_filter in [
        "tsq.status = 'ENABLED'",
        "tt.status = 'ENABLED'",
        "rp.status = 'ENABLED'",
        "ss.status = 'ENABLED'",
        "start_pier.status = 'ENABLED'",
        "end_pier.status = 'ENABLED'",
    ]:
        assert status_filter in query

    assert "JOIN pier start_pier ON start_pier.id = rp.start_pier_id" in query
    assert "JOIN pier end_pier ON end_pier.id = rp.end_pier_id" in query
    assert "(tsq.quota_total - tsq.quota_sold) AS quota_remaining" in query
    assert "quota_checked_in" not in query
