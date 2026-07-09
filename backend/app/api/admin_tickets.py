from fastapi import APIRouter, Depends, Request

from app.core.responses import success_response
from app.schemas.admin_tickets import AdminTicketDTO, AdminTicketSaveRequest
from app.schemas.common import ApiSuccessDTO
from app.services.admin_tickets import AdminTicketsService, get_admin_tickets_service

router = APIRouter(prefix="/api/admin/tickets", tags=["admin-tickets"])


@router.get("", response_model=ApiSuccessDTO[list[AdminTicketDTO]])
def list_admin_tickets(
    request: Request,
    admin_tickets_service: AdminTicketsService = Depends(get_admin_tickets_service),
) -> dict:
    tickets = admin_tickets_service.list_tickets(request)
    return success_response(request, [ticket.model_dump(by_alias=True, mode="json") for ticket in tickets])


@router.post("", response_model=ApiSuccessDTO[AdminTicketDTO])
def create_admin_ticket(
    payload: AdminTicketSaveRequest,
    request: Request,
    admin_tickets_service: AdminTicketsService = Depends(get_admin_tickets_service),
) -> dict:
    ticket = admin_tickets_service.create_ticket(payload, request)
    return success_response(request, ticket.model_dump(by_alias=True, mode="json"))


@router.patch("/{ticket_id}", response_model=ApiSuccessDTO[AdminTicketDTO])
def update_admin_ticket(
    ticket_id: int,
    payload: AdminTicketSaveRequest,
    request: Request,
    admin_tickets_service: AdminTicketsService = Depends(get_admin_tickets_service),
) -> dict:
    ticket = admin_tickets_service.update_ticket(ticket_id, payload, request)
    return success_response(request, ticket.model_dump(by_alias=True, mode="json"))


@router.delete("/{ticket_id}", response_model=ApiSuccessDTO[dict])
def delete_admin_ticket(
    ticket_id: int,
    request: Request,
    admin_tickets_service: AdminTicketsService = Depends(get_admin_tickets_service),
) -> dict:
    admin_tickets_service.delete_ticket(ticket_id, request)
    return success_response(request, {"deleted": True})
