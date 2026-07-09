from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal
from typing import Protocol

from app.core.db import connect_db


@dataclass(frozen=True)
class ProductRecord:
    product_id: int
    ticket_type_id: int
    scenic_spot_name: str
    product_name: str
    ticket_name: str
    ticket_category: str
    original_price: Decimal
    sale_price: Decimal
    description: str | None
    refund_rule: str | None
    real_name_required: bool
    trip_type: str
    raft_capacity: int
    start_pier_name: str
    end_pier_name: str
    window_phone: str


@dataclass(frozen=True)
class TimeSlotRecord:
    time_slot_id: int
    product_id: int
    ticket_type_id: int
    visit_date: date
    slot_start_time: time
    slot_end_time: time
    quota_remaining: int


class CatalogRepository(Protocol):
    def list_products(self) -> list[ProductRecord]:
        ...

    def list_time_slots(
        self,
        visit_date: date | None = None,
        ticket_type_id: int | None = None,
        product_id: int | None = None,
    ) -> list[TimeSlotRecord]:
        ...


def product_from_row(row: dict) -> ProductRecord:
    return ProductRecord(
        product_id=row["product_id"],
        ticket_type_id=row["ticket_type_id"],
        scenic_spot_name=row["scenic_spot_name"],
        product_name=row["product_name"],
        ticket_name=row["ticket_name"],
        ticket_category=row["ticket_category"],
        original_price=row["original_price"],
        sale_price=row["sale_price"],
        description=row["description"],
        refund_rule=row["refund_rule"],
        real_name_required=row["real_name_required"],
        trip_type=row["trip_type"],
        raft_capacity=row["raft_capacity"],
        start_pier_name=row["start_pier_name"],
        end_pier_name=row["end_pier_name"],
        window_phone=row["window_phone"],
    )


def time_slot_from_row(row: dict) -> TimeSlotRecord:
    return TimeSlotRecord(
        time_slot_id=row["time_slot_id"],
        product_id=row["product_id"],
        ticket_type_id=row["ticket_type_id"],
        visit_date=row["visit_date"],
        slot_start_time=row["slot_start_time"],
        slot_end_time=row["slot_end_time"],
        quota_remaining=max(row["quota_remaining"], 0),
    )


class PostgresCatalogRepository:
    def list_products(self) -> list[ProductRecord]:
        with connect_db() as connection:
            rows = connection.execute(
                """
                SELECT
                    rp.id AS product_id,
                    tt.id AS ticket_type_id,
                    ss.spot_name AS scenic_spot_name,
                    rp.product_name,
                    tt.ticket_name,
                    tt.ticket_category,
                    tt.original_price,
                    rp.sale_price,
                    tt.description,
                    tt.refund_rule,
                    tt.is_real_name_required AS real_name_required,
                    rp.trip_type,
                    rp.raft_capacity,
                    start_pier.pier_name AS start_pier_name,
                    end_pier.pier_name AS end_pier_name,
                    rp.window_phone
                FROM route_product rp
                JOIN ticket_type tt ON tt.id = rp.ticket_type_id
                JOIN scenic_spot ss ON ss.id = rp.scenic_spot_id
                JOIN pier start_pier ON start_pier.id = rp.start_pier_id
                JOIN pier end_pier ON end_pier.id = rp.end_pier_id
                WHERE rp.status = 'ENABLED'
                  AND tt.status = 'ENABLED'
                  AND ss.status = 'ENABLED'
                  AND start_pier.status = 'ENABLED'
                  AND end_pier.status = 'ENABLED'
                ORDER BY rp.id
                """
            ).fetchall()
        return [product_from_row(row) for row in rows]

    def list_time_slots(
        self,
        visit_date: date | None = None,
        ticket_type_id: int | None = None,
        product_id: int | None = None,
    ) -> list[TimeSlotRecord]:
        filters = [
            "tsq.status = 'ENABLED'",
            "tt.status = 'ENABLED'",
            "rp.status = 'ENABLED'",
            "ss.status = 'ENABLED'",
            "start_pier.status = 'ENABLED'",
            "end_pier.status = 'ENABLED'",
        ]
        params: list[object] = []
        if visit_date is not None:
            filters.append("tsq.visit_date = %s")
            params.append(visit_date)
        if ticket_type_id is not None:
            filters.append("tsq.ticket_type_id = %s")
            params.append(ticket_type_id)
        if product_id is not None:
            filters.append("rp.id = %s")
            params.append(product_id)

        with connect_db() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    tsq.id AS time_slot_id,
                    rp.id AS product_id,
                    tsq.ticket_type_id,
                    tsq.visit_date,
                    tsq.slot_start_time,
                    tsq.slot_end_time,
                    (tsq.quota_total - tsq.quota_sold) AS quota_remaining
                FROM time_slot_quota tsq
                JOIN ticket_type tt ON tt.id = tsq.ticket_type_id
                JOIN route_product rp ON rp.ticket_type_id = tt.id
                JOIN scenic_spot ss ON ss.id = tt.scenic_spot_id
                JOIN pier start_pier ON start_pier.id = rp.start_pier_id
                JOIN pier end_pier ON end_pier.id = rp.end_pier_id
                WHERE {" AND ".join(filters)}
                ORDER BY tsq.visit_date, tsq.slot_start_time, tsq.id
                """,
                tuple(params),
            ).fetchall()
        return [time_slot_from_row(row) for row in rows]


def get_catalog_repository() -> CatalogRepository:
    return PostgresCatalogRepository()
