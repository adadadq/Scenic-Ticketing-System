import re
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from app.schemas.auth import (
    CsrfPayloadDTO,
    LogoutPayloadDTO,
    VisitorLoginRequest,
    VisitorMeDTO,
    VisitorRegisterRequest,
)
from app.schemas.catalog import ProductPublicDTO, TimeSlotPublicDTO
from app.schemas.common import ApiFailureDTO, ApiSuccessDTO
from app.schemas.admin_exports import AdminExportJobDTO, AdminExportJobListDTO
from app.schemas.health import HealthDTO
from app.schemas.orders import OrderCreateItemRequest, OrderCreateRequest, OrderItemMeDTO, OrderMeDTO
from app.services.orders import ORDER_STATUS_FILTERS


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_TYPES_PATH = PROJECT_ROOT / "frontend" / "src" / "shared" / "api" / "types.ts"
FRONTEND_TYPES_DIR = FRONTEND_TYPES_PATH.parent


@dataclass(frozen=True)
class FrontendField:
    optional: bool
    type_text: str


def frontend_types_source() -> str:
    assert FRONTEND_TYPES_PATH.exists(), f"frontend API types file not found: {FRONTEND_TYPES_PATH}"
    return FRONTEND_TYPES_PATH.read_text(encoding="utf-8")


def frontend_source_for_type(type_name: str) -> tuple[str, Path]:
    source = frontend_types_source()
    if re.search(rf"export\s+type\s+{re.escape(type_name)}(?:<[^>]+>)?\s*=", source):
        return source, FRONTEND_TYPES_PATH

    for export_match in re.finditer(
        r"export\s+type\s+\{(?P<body>.*?)\}\s+from\s+['\"](?P<module>[^'\"]+)['\"]",
        source,
        flags=re.DOTALL,
    ):
        exported_types = {
            item.strip().split(" as ", maxsplit=1)[-1].strip()
            for item in export_match.group("body").split(",")
            if item.strip()
        }
        if type_name not in exported_types:
            continue
        module_path = FRONTEND_TYPES_DIR / f"{export_match.group('module')}.ts"
        assert module_path.exists(), f"frontend re-export source not found for {type_name}: {module_path}"
        return module_path.read_text(encoding="utf-8"), module_path

    return source, FRONTEND_TYPES_PATH


def frontend_object_type_fields(type_name: str) -> dict[str, FrontendField]:
    source, source_path = frontend_source_for_type(type_name)
    match = re.search(
        rf"export\s+type\s+{re.escape(type_name)}(?:<[^>]+>)?\s*=\s*\{{(?P<body>.*?)\n\}};?",
        source,
        flags=re.DOTALL,
    )
    assert match, f"frontend object type {type_name} not found in {source_path}"
    fields = {
        field_match.group("name"): FrontendField(
            optional=bool(field_match.group("optional")),
            type_text=field_match.group("type").strip().rstrip(";"),
        )
        for field_match in re.finditer(
            r"^\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?P<optional>\?)?:\s*(?P<type>.+?)\s*;?$",
            match.group("body"),
            flags=re.MULTILINE,
        )
    }
    assert fields, f"frontend object type {type_name} has no parseable fields in {source_path}"
    return fields


def frontend_string_union_values(type_name: str) -> set[str]:
    source, source_path = frontend_source_for_type(type_name)
    match = re.search(
        rf"export\s+type\s+{re.escape(type_name)}(?:<[^>]+>)?\s*=\s*(?P<body>.*?)(?:\nexport\s+type|\Z)",
        source,
        flags=re.DOTALL,
    )
    assert match, f"frontend union type {type_name} not found in {source_path}"
    return set(re.findall(r"['\"]([^'\"]+)['\"]", match.group("body")))


def pydantic_alias_fields(model_type: type[BaseModel]) -> set[str]:
    return {field.alias or name for name, field in model_type.model_fields.items()}


def assert_frontend_fields_match_pydantic(type_name: str, model_type: type[BaseModel]) -> None:
    frontend_fields = set(frontend_object_type_fields(type_name))
    backend_fields = pydantic_alias_fields(model_type)

    assert frontend_fields == backend_fields, (
        f"{type_name} does not match {model_type.__name__}: "
        f"missing_in_frontend={sorted(backend_fields - frontend_fields)}, "
        f"extra_in_frontend={sorted(frontend_fields - backend_fields)}"
    )


def test_visitor_me_dto_matches_frontend_auth_contract_without_identity_document():
    dto = VisitorMeDTO(
        visitor_id=7,
        visitor_name="张三",
        phone="13911112222",
        visitor_scope="REGISTERED",
        is_registered=True,
    )

    payload = dto.model_dump(by_alias=True, mode="json")

    assert payload == {
        "visitorId": 7,
        "visitorName": "张三",
        "phone": "13911112222",
        "visitorScope": "REGISTERED",
        "isRegistered": True,
    }
    assert "idNumber" not in payload
    assert "session" not in payload


def test_frontend_auth_types_match_backend_dto_fields():
    visitor = VisitorMeDTO(
        visitor_id=7,
        visitor_name="张三",
        phone="13911112222",
        visitor_scope="REGISTERED",
        is_registered=True,
    )

    assert set(frontend_object_type_fields("VisitorMe")) == set(visitor.model_dump(by_alias=True, mode="json"))
    assert_frontend_fields_match_pydantic("ApiSuccess", ApiSuccessDTO)
    assert_frontend_fields_match_pydantic("ApiFailure", ApiFailureDTO)
    assert_frontend_fields_match_pydantic("CsrfPayload", CsrfPayloadDTO)
    assert_frontend_fields_match_pydantic("LogoutPayload", LogoutPayloadDTO)
    assert_frontend_fields_match_pydantic("VisitorLoginRequest", VisitorLoginRequest)
    assert_frontend_fields_match_pydantic("VisitorRegisterRequest", VisitorRegisterRequest)


def test_frontend_health_type_matches_backend_process_health_dto():
    dto = HealthDTO(status="ok", service="scenic-ticketing", environment="test")

    payload = dto.model_dump(by_alias=True, mode="json")
    frontend_fields = frontend_object_type_fields("HealthPayload")

    assert payload == {
        "status": "ok",
        "service": "scenic-ticketing",
        "environment": "test",
    }
    assert_frontend_fields_match_pydantic("HealthPayload", HealthDTO)
    assert frontend_fields["status"] == FrontendField(optional=False, type_text="'ok'")
    assert frontend_fields["service"] == FrontendField(optional=False, type_text="string")
    assert frontend_fields["environment"] == FrontendField(optional=False, type_text="string")


def test_auth_request_dtos_forbid_extra_client_controlled_fields():
    login_payload = {
        "username": "zhangsan_001",
        "password": "Visitor123",
    }
    register_payload = {
        "username": "zhangsan_001",
        "password": "Visitor123",
        "phone": "13911112222",
    }

    login_request = VisitorLoginRequest.model_validate(login_payload)
    register_request = VisitorRegisterRequest.model_validate(register_payload)

    assert login_request.username == "zhangsan_001"
    assert register_request.phone == "13911112222"

    with pytest.raises(ValidationError) as login_error:
        VisitorLoginRequest.model_validate(login_payload | {"visitorId": 999})
    assert login_error.value.errors()[0]["loc"] == ("visitorId",)

    with pytest.raises(ValidationError) as register_error:
        VisitorRegisterRequest.model_validate(register_payload | {"sessionToken": "client-controlled"})
    assert register_error.value.errors()[0]["loc"] == ("sessionToken",)


def test_catalog_public_dtos_match_frontend_contract_without_internal_fields():
    product = ProductPublicDTO(
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
    slot = TimeSlotPublicDTO(
        time_slot_id=100,
        product_id=1,
        ticket_type_id=10,
        visit_date=date(2026, 7, 1),
        slot_start_time=time(8, 30),
        slot_end_time=time(10, 30),
        quota_remaining=35,
    )

    product_payload = product.model_dump(by_alias=True, mode="json")
    slot_payload = slot.model_dump(by_alias=True, mode="json")

    assert set(product_payload) == {
        "productId",
        "ticketTypeId",
        "scenicSpotName",
        "productName",
        "ticketName",
        "ticketCategory",
        "originalPrice",
        "salePrice",
        "description",
        "refundRule",
        "realNameRequired",
        "tripType",
        "raftCapacity",
        "startPierName",
        "endPierName",
        "windowPhone",
    }
    assert set(slot_payload) == {
        "timeSlotId",
        "productId",
        "ticketTypeId",
        "visitDate",
        "slotStartTime",
        "slotEndTime",
        "quotaRemaining",
    }
    assert "status" not in product_payload
    assert product_payload["originalPrice"] == "168.00"
    assert product_payload["salePrice"] == "128.00"
    assert "quotaTotal" not in slot_payload
    assert "quotaSold" not in slot_payload
    assert slot_payload["visitDate"] == "2026-07-01"
    assert slot_payload["slotStartTime"] == "08:30:00"


def test_frontend_catalog_types_match_backend_public_dto_fields():
    product = ProductPublicDTO(
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
    slot = TimeSlotPublicDTO(
        time_slot_id=100,
        product_id=1,
        ticket_type_id=10,
        visit_date=date(2026, 7, 1),
        slot_start_time=time(8, 30),
        slot_end_time=time(10, 30),
        quota_remaining=35,
    )

    product_payload = product.model_dump(by_alias=True, mode="json")
    slot_payload = slot.model_dump(by_alias=True, mode="json")
    product_fields = frontend_object_type_fields("ProductPublic")

    assert set(product_fields) == set(product_payload)
    assert product_fields["description"].optional is True
    assert product_fields["description"].type_text == "string | null"
    assert product_fields["refundRule"].optional is True
    assert product_fields["refundRule"].type_text == "string | null"
    assert set(frontend_object_type_fields("TimeSlotPublic")) == set(slot_payload)


def test_order_create_request_accepts_frontend_payload_and_forbids_visitor_assignment():
    payload = {
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

    request = OrderCreateRequest.model_validate(payload)

    assert request.buyer_phone == "13911112222"
    assert request.items[0].product_id == 1
    with pytest.raises(ValidationError) as top_level_error:
        OrderCreateRequest.model_validate(payload | {"visitorId": 999})
    assert top_level_error.value.errors()[0]["loc"] == ("visitorId",)

    nested_payload = payload | {
        "items": [
            payload["items"][0] | {
                "visitorId": 999,
                "status": "ENABLED",
                "ticketCode": "TKSHOULDNOTBESENT",
            }
        ]
    }
    with pytest.raises(ValidationError) as nested_error:
        OrderCreateRequest.model_validate(nested_payload)
    assert {error["loc"] for error in nested_error.value.errors()} == {
        ("items", 0, "visitorId"),
        ("items", 0, "status"),
        ("items", 0, "ticketCode"),
    }


def test_order_me_dto_matches_frontend_order_contract_and_omits_pending_ticket_code():
    dto = OrderMeDTO(
        order_no="O202607010900000001",
        buyer_name="张三",
        buyer_phone="139****2222",
        order_status="CREATED",
        payment_status="UNPAID",
        total_amount=Decimal("256.00"),
        payable_amount=Decimal("256.00"),
        order_time=datetime.fromisoformat("2026-07-01T09:00:00+00:00"),
        items=[
            OrderItemMeDTO(
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
                item_status="PENDING_PAYMENT",
                ticket_code=None,
                passenger_name="张三",
                passenger_id_type="ID_CARD",
                passenger_id_number_masked="110********02X",
                passenger_phone_masked="139****2222",
            )
        ],
    )

    payload = dto.model_dump(by_alias=True, exclude_none=True, mode="json")

    assert set(payload) == {
        "orderNo",
        "buyerName",
        "buyerPhone",
        "orderStatus",
        "paymentStatus",
        "totalAmount",
        "payableAmount",
        "orderTime",
        "canSelfRefund",
        "items",
    }
    assert set(payload["items"][0]) == {
        "itemNo",
        "productId",
        "ticketTypeId",
        "productName",
        "ticketName",
        "timeSlotId",
        "visitDate",
        "slotStartTime",
        "slotEndTime",
        "originalPrice",
        "finalPrice",
        "itemStatus",
        "passengerName",
        "passengerIdType",
        "passengerIdNumberMasked",
        "passengerPhoneMasked",
    }
    assert "visitorId" not in payload
    assert "idNumber" not in payload
    assert payload["totalAmount"] == "256.00"
    assert payload["payableAmount"] == "256.00"
    assert payload["items"][0]["originalPrice"] == "168.00"
    assert payload["items"][0]["finalPrice"] == "128.00"
    assert "ticketCode" not in payload["items"][0]


def test_frontend_order_types_match_backend_dto_fields_and_filters():
    order = OrderMeDTO(
        order_no="O202607010900000001",
        buyer_name="张三",
        buyer_phone="139****2222",
        order_status="PAID",
        payment_status="PAID",
        total_amount=Decimal("256.00"),
        payable_amount=Decimal("256.00"),
        order_time=datetime.fromisoformat("2026-07-01T09:00:00+00:00"),
        refund_deadline=datetime.fromisoformat("2026-06-30T18:00:00+08:00"),
        items=[
            OrderItemMeDTO(
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
                item_status="UNUSED",
                ticket_code="TKRANDOMABC123",
                passenger_name="张三",
                passenger_id_type="ID_CARD",
                passenger_id_number_masked="110********02X",
                passenger_phone_masked="139****2222",
                raft_no=1,
                raft_seat_no=1,
                raft_assigned_at=datetime.fromisoformat("2026-07-01T10:00:00+00:00"),
            )
        ],
    )

    payload = order.model_dump(by_alias=True, exclude_none=True, mode="json")
    item_payload = payload["items"][0]
    item_fields = frontend_object_type_fields("OrderItemMe")

    assert_frontend_fields_match_pydantic("OrderCreateItemRequest", OrderCreateItemRequest)
    assert_frontend_fields_match_pydantic("OrderCreateRequest", OrderCreateRequest)
    assert set(frontend_object_type_fields("OrderMe")) == set(payload)
    assert set(item_fields) == set(item_payload)
    assert item_fields["ticketCode"].optional is True
    assert frontend_string_union_values("OrderStatusFilter") == ORDER_STATUS_FILTERS


def test_frontend_admin_export_job_types_match_backend_dto_fields():
    assert_frontend_fields_match_pydantic("AdminExportJob", AdminExportJobDTO)
    assert_frontend_fields_match_pydantic("AdminExportJobList", AdminExportJobListDTO)


def test_paid_order_item_dto_includes_ticket_code_for_frontend_ticket_display():
    dto = OrderItemMeDTO(
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
        item_status="UNUSED",
        ticket_code="TKRANDOMABC123",
        passenger_name="张三",
        passenger_id_type="ID_CARD",
        passenger_id_number_masked="110********02X",
        passenger_phone_masked="139****2222",
    )

    payload = dto.model_dump(by_alias=True, exclude_none=True, mode="json")

    assert payload["ticketCode"] == "TKRANDOMABC123"
    assert payload["itemStatus"] == "UNUSED"
