from datetime import date

from fastapi import Depends

from app.repositories.catalog import CatalogRepository, get_catalog_repository
from app.schemas.catalog import ProductPublicDTO, TimeSlotPublicDTO


class CatalogService:
    def __init__(self, repository: CatalogRepository):
        self.repository = repository

    def list_products(self) -> list[ProductPublicDTO]:
        return [
            ProductPublicDTO(
                product_id=product.product_id,
                ticket_type_id=product.ticket_type_id,
                scenic_spot_name=product.scenic_spot_name,
                product_name=product.product_name,
                ticket_name=product.ticket_name,
                ticket_category=product.ticket_category,
                original_price=product.original_price,
                sale_price=product.sale_price,
                description=product.description,
                refund_rule=product.refund_rule,
                real_name_required=product.real_name_required,
                trip_type=product.trip_type,
                raft_capacity=product.raft_capacity,
                start_pier_name=product.start_pier_name,
                end_pier_name=product.end_pier_name,
                window_phone=product.window_phone,
            )
            for product in self.repository.list_products()
        ]

    def list_time_slots(
        self,
        visit_date: date | None = None,
        ticket_type_id: int | None = None,
        product_id: int | None = None,
    ) -> list[TimeSlotPublicDTO]:
        return [
            TimeSlotPublicDTO(
                time_slot_id=slot.time_slot_id,
                product_id=slot.product_id,
                ticket_type_id=slot.ticket_type_id,
                visit_date=slot.visit_date,
                slot_start_time=slot.slot_start_time,
                slot_end_time=slot.slot_end_time,
                quota_remaining=slot.quota_remaining,
            )
            for slot in self.repository.list_time_slots(
                visit_date=visit_date,
                ticket_type_id=ticket_type_id,
                product_id=product_id,
            )
        ]


def get_catalog_service(repository: CatalogRepository = Depends(get_catalog_repository)) -> CatalogService:
    return CatalogService(repository)
