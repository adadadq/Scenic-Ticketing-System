from datetime import date

from fastapi import APIRouter, Depends, Query, Request

from app.core.errors import AppError
from app.core.responses import success_response
from app.schemas.catalog import ProductPublicDTO, TimeSlotPublicDTO
from app.schemas.common import ApiSuccessDTO
from app.services.catalog import CatalogService, get_catalog_service

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.get("/products", response_model=ApiSuccessDTO[list[ProductPublicDTO]])
def list_products(request: Request, catalog_service: CatalogService = Depends(get_catalog_service)) -> dict:
    try:
        products = catalog_service.list_products()
    except Exception as exc:
        raise AppError(503, "CATALOG_UNAVAILABLE", "票品接口暂不可用") from exc
    return success_response(
        request,
        [product.model_dump(by_alias=True, mode="json") for product in products],
    )


@router.get("/time-slots", response_model=ApiSuccessDTO[list[TimeSlotPublicDTO]])
def list_time_slots(
    request: Request,
    visit_date: date | None = Query(default=None, alias="visitDate"),
    ticket_type_id: int | None = Query(default=None, alias="ticketTypeId", gt=0),
    product_id: int | None = Query(default=None, alias="productId", gt=0),
    catalog_service: CatalogService = Depends(get_catalog_service),
) -> dict:
    try:
        slots = catalog_service.list_time_slots(
            visit_date=visit_date,
            ticket_type_id=ticket_type_id,
            product_id=product_id,
        )
    except Exception as exc:
        raise AppError(503, "TIME_SLOTS_UNAVAILABLE", "时段接口暂不可用") from exc
    return success_response(
        request,
        [slot.model_dump(by_alias=True, mode="json") for slot in slots],
    )
