from fastapi import Depends, Request

from app.core.errors import AppError
from app.repositories.admin_tickets import AdminTicketRecord, AdminTicketsRepository, get_admin_tickets_repository
from app.schemas.admin_tickets import AdminTicketDTO, AdminTicketSaveRequest
from app.services.auth import AdminAuthService, get_admin_auth_service


class AdminTicketsService:
    def __init__(self, repository: AdminTicketsRepository, admin_auth_service: AdminAuthService):
        self.repository = repository
        self.admin_auth_service = admin_auth_service

    def list_tickets(self, request: Request) -> list[AdminTicketDTO]:
        self.admin_auth_service.current_session_admin(request)
        return [self.to_dto(ticket) for ticket in self.repository.list_tickets()]

    def create_ticket(self, payload: AdminTicketSaveRequest, request: Request) -> AdminTicketDTO:
        self.admin_auth_service.require_super_admin(request)
        return self.to_dto(self._save(None, payload))

    def update_ticket(self, ticket_id: int, payload: AdminTicketSaveRequest, request: Request) -> AdminTicketDTO:
        self.admin_auth_service.require_super_admin(request)
        try:
            return self.to_dto(self._save(ticket_id, payload))
        except LookupError as exc:
            raise AppError(404, "ADMIN_TICKET_NOT_FOUND", "票种不存在") from exc

    def delete_ticket(self, ticket_id: int, request: Request) -> None:
        self.admin_auth_service.require_super_admin(request)
        self.repository.delete_ticket(ticket_id)

    def _save(self, ticket_id: int | None, payload: AdminTicketSaveRequest) -> AdminTicketRecord:
        return self.repository.save_ticket(
            ticket_id,
            name=payload.name,
            ticket_type=payload.type,
            route=payload.route,
            sale_price=payload.sale_price,
            stock=payload.stock,
            status=payload.status,
            description=payload.description,
            date_from=payload.date_from,
            date_to=payload.date_to,
            slot_quota=payload.slot_quota,
            slot_quotas=tuple(
                (slot.slot_start_time, slot.slot_end_time, slot.quota)
                for slot in (payload.slot_quotas or [])
            ),
        )

    @staticmethod
    def to_dto(ticket: AdminTicketRecord) -> AdminTicketDTO:
        return AdminTicketDTO(
            id=ticket.id,
            name=ticket.name,
            type=ticket.type,
            route=ticket.route,
            sale_price=ticket.sale_price,
            stock=ticket.stock,
            allocated_quota=ticket.allocated_quota,
            status=ticket.status,
            description=ticket.description,
            date_from=ticket.date_from,
            date_to=ticket.date_to,
            slot_quota=ticket.slot_quota,
            slot_quotas=[
                {"slotStartTime": start, "slotEndTime": end, "quota": quota}
                for start, end, quota in ticket.slot_quotas
            ],
        )


def get_admin_tickets_service(
    repository: AdminTicketsRepository = Depends(get_admin_tickets_repository),
    admin_auth_service: AdminAuthService = Depends(get_admin_auth_service),
) -> AdminTicketsService:
    return AdminTicketsService(repository, admin_auth_service)
