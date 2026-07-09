from datetime import date, time
from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import create_app
from app.repositories.catalog import ProductRecord, TimeSlotRecord, get_catalog_repository
from app.repositories.auth import get_auth_repository
from app.repositories.orders import get_order_repository
from test_visitor_flow_api import FlowAuthRepository, FlowCatalogRepository, FlowOrderRepository, order_payload


SUCCESS_KEYS = {"success", "data", "request_id"}


class SuccessContractCatalogRepository:
    def list_products(self) -> list[ProductRecord]:
        return [
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
            )
        ]

    def list_time_slots(
        self,
        visit_date: date | None = None,
        ticket_type_id: int | None = None,
        product_id: int | None = None,
    ) -> list[TimeSlotRecord]:
        slot = TimeSlotRecord(
            time_slot_id=100,
            product_id=1,
            ticket_type_id=10,
            visit_date=date(2026, 7, 1),
            slot_start_time=time(8, 30),
            slot_end_time=time(10, 30),
            quota_remaining=35,
        )
        if visit_date is not None and slot.visit_date != visit_date:
            return []
        if ticket_type_id is not None and slot.ticket_type_id != ticket_type_id:
            return []
        if product_id is not None and slot.product_id != product_id:
            return []
        return [slot]


def assert_success_contract(response, *, request_id: str | None = None) -> None:
    body = response.json()

    assert response.status_code == 200
    assert set(body) == SUCCESS_KEYS
    assert body["success"] is True
    assert "data" in body
    assert isinstance(body["request_id"], str)
    assert body["request_id"]
    assert response.headers["x-request-id"] == body["request_id"]
    if request_id is not None:
        assert body["request_id"] == request_id


def test_success_contract_generates_request_id_when_header_is_absent():
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert_success_contract(response)
    assert response.json()["data"]["status"] == "ok"


def test_success_contract_preserves_client_request_id_for_catalog():
    app = create_app()
    app.dependency_overrides[get_catalog_repository] = lambda: SuccessContractCatalogRepository()
    client = TestClient(app)

    response = client.get("/api/catalog/products", headers={"x-request-id": "catalog-success"})

    assert_success_contract(response, request_id="catalog-success")
    assert response.json()["data"][0]["productId"] == 1


def test_csrf_success_contract_sets_cookie_without_returning_token():
    client = TestClient(create_app())

    response = client.get("/api/auth/csrf", headers={"x-request-id": "csrf-success"})

    assert_success_contract(response, request_id="csrf-success")
    assert response.json()["data"] == {"headerName": "x-csrf-token"}
    assert "scenic_csrf=" in response.headers["set-cookie"]


def test_current_frontend_success_endpoints_share_response_contract():
    auth_repo = FlowAuthRepository()
    catalog_repo = FlowCatalogRepository()
    order_repo = FlowOrderRepository()
    app = create_app()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repo
    app.dependency_overrides[get_catalog_repository] = lambda: catalog_repo
    app.dependency_overrides[get_order_repository] = lambda: order_repo
    client = TestClient(app)

    csrf_response = client.get("/api/auth/csrf", headers={"x-request-id": "contract-csrf"})
    csrf_headers = {"x-csrf-token": client.cookies["scenic_csrf"]}
    register_response = client.post(
        "/api/auth/visitor/register",
        json={
            "username": "zhangsan_001",
            "password": "Visitor123",
            "phone": "13911112222",
        },
        headers=csrf_headers | {"x-request-id": "contract-register"},
    )
    register_logout_response = client.post(
        "/api/auth/logout",
        headers=csrf_headers | {"x-request-id": "contract-register-logout"},
    )
    csrf_response_after_logout = client.get("/api/auth/csrf", headers={"x-request-id": "contract-csrf-login"})
    login_csrf_headers = {"x-csrf-token": client.cookies["scenic_csrf"]}
    login_response = client.post(
        "/api/auth/visitor/login",
        json={"username": "zhangsan_001", "password": "Visitor123"},
        headers=login_csrf_headers | {"x-request-id": "contract-login"},
    )
    me_response = client.get("/api/auth/me", headers={"x-request-id": "contract-me"})
    products_response = client.get("/api/catalog/products", headers={"x-request-id": "contract-products"})
    slots_response = client.get(
        "/api/catalog/time-slots",
        params={"visitDate": "2026-07-01", "ticketTypeId": 10, "productId": 1},
        headers={"x-request-id": "contract-slots"},
    )
    create_response = client.post(
        "/api/orders",
        json=order_payload(),
        headers=login_csrf_headers | {"x-request-id": "contract-create-order"},
    )
    order_no = create_response.json()["data"]["orderNo"]
    cancel_create_response = client.post(
        "/api/orders",
        json=order_payload(),
        headers=login_csrf_headers | {"x-request-id": "contract-create-cancel-order"},
    )
    cancel_order_no = cancel_create_response.json()["data"]["orderNo"]
    cancel_response = client.post(
        f"/api/orders/{cancel_order_no}/cancel",
        headers=login_csrf_headers | {"x-request-id": "contract-cancel-order"},
    )
    pay_response = client.post(
        f"/api/orders/{order_no}/pay",
        headers=login_csrf_headers
        | {
            "Idempotency-Key": "contract-pay",
            "x-request-id": "contract-pay-order",
        },
    )
    list_response = client.get("/api/me/orders", headers={"x-request-id": "contract-list-orders"})
    detail_response = client.get(f"/api/me/orders/{order_no}", headers={"x-request-id": "contract-order-detail"})
    logout_response = client.post("/api/auth/logout", headers=login_csrf_headers | {"x-request-id": "contract-logout"})

    responses = [
        ("contract-csrf", csrf_response),
        ("contract-register", register_response),
        ("contract-register-logout", register_logout_response),
        ("contract-csrf-login", csrf_response_after_logout),
        ("contract-login", login_response),
        ("contract-me", me_response),
        ("contract-products", products_response),
        ("contract-slots", slots_response),
        ("contract-create-order", create_response),
        ("contract-create-cancel-order", cancel_create_response),
        ("contract-cancel-order", cancel_response),
        ("contract-pay-order", pay_response),
        ("contract-list-orders", list_response),
        ("contract-order-detail", detail_response),
        ("contract-logout", logout_response),
    ]

    for request_id, response in responses:
        assert_success_contract(response, request_id=request_id)
