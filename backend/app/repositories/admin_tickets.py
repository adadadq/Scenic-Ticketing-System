from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Protocol

from app.core.admin_audit import AdminAuditContext
from app.core.db import connect_db, transaction


DEFAULT_SLOTS = (
    ("08:30", "10:30"),
    ("10:30", "12:30"),
    ("12:30", "13:30"),
    ("13:30", "15:30"),
    ("15:30", "17:30"),
    ("17:30", "18:30"),
)


@dataclass(frozen=True)
class AdminTicketRecord:
    id: int
    name: str
    type: str
    route: str
    sale_price: Decimal
    stock: int
    allocated_quota: int
    status: str
    description: str | None
    date_from: date | None
    date_to: date | None
    slot_quota: int
    slot_quotas: tuple[tuple[str, str, int], ...]


class AdminTicketsRepository(Protocol):
    def list_tickets(self) -> list[AdminTicketRecord]:
        ...

    def save_ticket(
        self,
        ticket_id: int | None,
        *,
        name: str,
        ticket_type: str,
        route: str,
        sale_price: Decimal,
        stock: int,
        status: str,
        description: str | None,
        date_from: date | None,
        date_to: date | None,
        slot_quota: int,
        slot_quotas: tuple[tuple[str, str, int], ...],
        audit: AdminAuditContext,
    ) -> AdminTicketRecord:
        ...

    def delete_ticket(self, ticket_id: int, audit: AdminAuditContext) -> None:
        ...


def _dates_between(start: date, end: date) -> list[date]:
    days = (end - start).days + 1
    return [start + timedelta(days=index) for index in range(days)]


def _default_slot_quotas(slot_quota: int) -> tuple[tuple[str, str, int], ...]:
    return tuple((start, end, slot_quota) for start, end in DEFAULT_SLOTS)


def _record(row: dict, slot_quotas: tuple[tuple[str, str, int], ...] | None = None) -> AdminTicketRecord:
    fallback_slot_quota = row["slot_quota"] or 40
    return AdminTicketRecord(
        id=row["id"],
        name=row["name"],
        type=row["type"],
        route=row["route"],
        sale_price=row["sale_price"],
        stock=row["stock"] or 0,
        allocated_quota=row["allocated_quota"] or 0,
        status=row["status"],
        description=row["description"],
        date_from=row["date_from"],
        date_to=row["date_to"],
        slot_quota=fallback_slot_quota,
        slot_quotas=slot_quotas or _default_slot_quotas(fallback_slot_quota),
    )


class PostgresAdminTicketsRepository:
    def list_tickets(self) -> list[AdminTicketRecord]:
        with connect_db() as connection:
            rows = connection.execute(
                """
                SELECT
                    tt.id,
                    tt.ticket_name AS name,
                    tt.ticket_category AS type,
                    COALESCE(rp.product_name, tt.ticket_name) AS route,
                    COALESCE(rp.sale_price, tt.sale_price) AS sale_price,
                    COALESCE(SUM(tsq.quota_total), 0)::INT AS stock,
                    COALESCE(SUM(GREATEST(tsq.quota_total - tsq.quota_sold, 0)), 0)::INT AS allocated_quota,
                    CASE WHEN tt.status = 'ENABLED' THEN 'ON_SALE' ELSE 'OFF_SALE' END AS status,
                    tt.description,
                    MIN(tsq.visit_date) AS date_from,
                    MAX(tsq.visit_date) AS date_to,
                    COALESCE(MAX(tsq.quota_total), 40)::INT AS slot_quota
                FROM ticket_type tt
                LEFT JOIN route_product rp ON rp.ticket_type_id = tt.id
                LEFT JOIN time_slot_quota tsq ON tsq.ticket_type_id = tt.id AND tsq.status = 'ENABLED'
                GROUP BY tt.id, rp.product_name, rp.sale_price
                ORDER BY tt.id
                """
            ).fetchall()
            slot_rows = connection.execute(
                """
                SELECT
                    ticket_type_id,
                    TO_CHAR(slot_start_time, 'HH24:MI') AS slot_start_time,
                    TO_CHAR(slot_end_time, 'HH24:MI') AS slot_end_time,
                    MAX(quota_total)::INT AS quota
                FROM time_slot_quota
                WHERE status = 'ENABLED'
                GROUP BY ticket_type_id, slot_start_time, slot_end_time
                ORDER BY slot_start_time, slot_end_time
                """
            ).fetchall()
        slot_map: dict[int, list[tuple[str, str, int]]] = {}
        for slot in slot_rows:
            slot_map.setdefault(slot["ticket_type_id"], []).append(
                (slot["slot_start_time"], slot["slot_end_time"], slot["quota"])
            )
        return [_record(row, tuple(slot_map.get(row["id"], ()))) for row in rows]

    def save_ticket(
        self,
        ticket_id: int | None,
        *,
        name: str,
        ticket_type: str,
        route: str,
        sale_price: Decimal,
        stock: int,
        status: str,
        description: str | None,
        date_from: date | None,
        date_to: date | None,
        slot_quota: int,
        slot_quotas: tuple[tuple[str, str, int], ...],
        audit: AdminAuditContext,
    ) -> AdminTicketRecord:
        db_status = "ENABLED" if status == "ON_SALE" else "DISABLED"
        next_slot_quotas = slot_quotas or _default_slot_quotas(slot_quota)
        with connect_db() as connection:
            with transaction(connection):
                if ticket_id:
                    row = connection.execute(
                        """
                        UPDATE ticket_type
                        SET ticket_name = %s,
                            ticket_category = %s,
                            original_price = %s,
                            sale_price = %s,
                            description = %s,
                            status = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        RETURNING id
                        """,
                        (name, ticket_type, sale_price, sale_price, description, db_status, ticket_id),
                    ).fetchone()
                    if not row:
                        raise LookupError("ticket not found")
                    saved_id = row["id"]
                else:
                    row = connection.execute(
                        """
                        INSERT INTO ticket_type (
                            scenic_spot_id, ticket_name, ticket_category, original_price, sale_price, description, status
                        )
                        VALUES (1, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (name, ticket_type, sale_price, sale_price, description, db_status),
                    ).fetchone()
                    saved_id = row["id"]

                cursor = connection.execute(
                    """
                    UPDATE route_product
                    SET product_name = %s,
                        sale_price = %s,
                        status = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE ticket_type_id = %s
                    """,
                    (route, sale_price, db_status, saved_id),
                )
                if cursor.rowcount == 0:
                    connection.execute(
                        """
                        INSERT INTO route_product (
                            scenic_spot_id, ticket_type_id, product_name, raft_capacity, trip_type,
                            start_pier_id, end_pier_id, window_phone, sale_price, status
                        )
                        VALUES (1, %s, %s, 2, 'ONE_WAY', 1, 2, '0773-1234567', %s, %s)
                        """,
                        (saved_id, route, sale_price, db_status),
                    )

                if date_from and date_to:
                    connection.execute(
                        """
                        UPDATE time_slot_quota
                        SET status = 'DISABLED', updated_at = CURRENT_TIMESTAMP
                        WHERE ticket_type_id = %s
                          AND (visit_date < %s OR visit_date > %s)
                        """,
                        (saved_id, date_from, date_to),
                    )
                    for visit_date in _dates_between(date_from, date_to):
                        for slot_start, slot_end, quota in next_slot_quotas:
                            _upsert_time_slot_quota(
                                connection,
                                ticket_type_id=saved_id,
                                visit_date=visit_date,
                                slot_start=slot_start,
                                slot_end=slot_end,
                                quota=quota,
                                status=db_status,
                            )
                elif stock:
                    today = date.today()
                    per_slot = max(1, stock // len(next_slot_quotas))
                    for slot_start, slot_end, quota in next_slot_quotas:
                        _upsert_time_slot_quota(
                            connection,
                            ticket_type_id=saved_id,
                            visit_date=today,
                            slot_start=slot_start,
                            slot_end=slot_end,
                            quota=quota if slot_quotas else per_slot,
                            status=db_status,
                        )

                row = connection.execute(
                    """
                    SELECT
                        tt.id,
                        tt.ticket_name AS name,
                        tt.ticket_category AS type,
                        COALESCE(rp.product_name, tt.ticket_name) AS route,
                        COALESCE(rp.sale_price, tt.sale_price) AS sale_price,
                        COALESCE(SUM(tsq.quota_total), 0)::INT AS stock,
                        COALESCE(SUM(GREATEST(tsq.quota_total - tsq.quota_sold, 0)), 0)::INT AS allocated_quota,
                        CASE WHEN tt.status = 'ENABLED' THEN 'ON_SALE' ELSE 'OFF_SALE' END AS status,
                        tt.description,
                        MIN(tsq.visit_date) AS date_from,
                        MAX(tsq.visit_date) AS date_to,
                        COALESCE(MAX(tsq.quota_total), %s)::INT AS slot_quota
                    FROM ticket_type tt
                    LEFT JOIN route_product rp ON rp.ticket_type_id = tt.id
                    LEFT JOIN time_slot_quota tsq ON tsq.ticket_type_id = tt.id AND tsq.status = 'ENABLED'
                    WHERE tt.id = %s
                    GROUP BY tt.id, rp.product_name, rp.sale_price
                    """,
                    (slot_quota, saved_id),
                ).fetchone()
                slot_rows = connection.execute(
                    """
                    SELECT
                        TO_CHAR(slot_start_time, 'HH24:MI') AS slot_start_time,
                        TO_CHAR(slot_end_time, 'HH24:MI') AS slot_end_time,
                        MAX(quota_total)::INT AS quota
                    FROM time_slot_quota
                    WHERE ticket_type_id = %s AND status = 'ENABLED'
                    GROUP BY slot_start_time, slot_end_time
                    ORDER BY slot_start_time, slot_end_time
                    """,
                    (saved_id,),
                ).fetchall()
                self._insert_audit_log(
                    connection,
                    ticket_id=saved_id,
                    ticket_name=name,
                    action="UPDATE" if ticket_id else "CREATE",
                    audit=audit,
                )
        return _record(
            row,
            tuple((slot["slot_start_time"], slot["slot_end_time"], slot["quota"]) for slot in slot_rows),
        )

    def delete_ticket(self, ticket_id: int, audit: AdminAuditContext) -> None:
        with connect_db() as connection:
            with transaction(connection):
                row = connection.execute(
                    "SELECT ticket_name FROM ticket_type WHERE id = %s",
                    (ticket_id,),
                ).fetchone()
                if not row:
                    raise LookupError("ticket not found")
                connection.execute("UPDATE time_slot_quota SET status = 'DISABLED', updated_at = CURRENT_TIMESTAMP WHERE ticket_type_id = %s", (ticket_id,))
                connection.execute("UPDATE route_product SET status = 'DISABLED', updated_at = CURRENT_TIMESTAMP WHERE ticket_type_id = %s", (ticket_id,))
                connection.execute("UPDATE ticket_type SET status = 'DISABLED', updated_at = CURRENT_TIMESTAMP WHERE id = %s", (ticket_id,))
                self._insert_audit_log(
                    connection,
                    ticket_id=ticket_id,
                    ticket_name=row["ticket_name"],
                    action="DELETE",
                    audit=audit,
                )

    @staticmethod
    def _insert_audit_log(connection, *, ticket_id: int, ticket_name: str, action: str, audit: AdminAuditContext) -> None:
        connection.execute(
            """
            INSERT INTO admin_ticket_audit_log (
                ticket_type_id,
                ticket_name,
                action,
                operator_admin_user_id,
                operator_username,
                operator_display_name,
                request_id,
                source_ip,
                device_id,
                admin_session_id,
                user_agent
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                ticket_id,
                ticket_name,
                action,
                audit.admin_user_id,
                audit.operator_username,
                audit.operator_display_name,
                audit.request_id,
                audit.source_ip,
                audit.device_id,
                audit.admin_session_id,
                audit.user_agent,
            ),
        )


def _upsert_time_slot_quota(
    connection,
    *,
    ticket_type_id: int,
    visit_date: date,
    slot_start: str,
    slot_end: str,
    quota: int,
    status: str,
) -> None:
    cursor = connection.execute(
        """
        UPDATE time_slot_quota
        SET quota_total = GREATEST(%s, quota_sold),
            status = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE ticket_type_id = %s
          AND visit_date = %s
          AND slot_start_time = %s
          AND slot_end_time = %s
        """,
        (quota, status, ticket_type_id, visit_date, slot_start, slot_end),
    )
    if cursor.rowcount == 0:
        connection.execute(
            """
            INSERT INTO time_slot_quota (
                ticket_type_id, visit_date, slot_start_time, slot_end_time, quota_total, status
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (ticket_type_id, visit_date, slot_start, slot_end, quota, status),
        )


def get_admin_tickets_repository() -> AdminTicketsRepository:
    return PostgresAdminTicketsRepository()
