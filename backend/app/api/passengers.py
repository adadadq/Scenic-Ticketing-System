from fastapi import APIRouter, Depends, Request

from app.core.responses import success_response
from app.schemas.common import ApiSuccessDTO
from app.schemas.passengers import PassengerTemplateDTO, PassengerTemplateRequest
from app.services.passengers import PassengerTemplateService, get_passenger_template_service

router = APIRouter(prefix="/api/me/passenger-templates", tags=["passenger-templates"])


@router.get("", response_model=ApiSuccessDTO[list[PassengerTemplateDTO]])
def list_passenger_templates(
    request: Request,
    passenger_service: PassengerTemplateService = Depends(get_passenger_template_service),
) -> dict:
    templates = passenger_service.list_templates(request)
    return success_response(request, [template.model_dump(by_alias=True, mode="json") for template in templates])


@router.post("", response_model=ApiSuccessDTO[PassengerTemplateDTO])
def create_passenger_template(
    payload: PassengerTemplateRequest,
    request: Request,
    passenger_service: PassengerTemplateService = Depends(get_passenger_template_service),
) -> dict:
    template = passenger_service.create_template(payload, request)
    return success_response(request, template.model_dump(by_alias=True, mode="json"))


@router.patch("/{template_id}", response_model=ApiSuccessDTO[PassengerTemplateDTO])
def update_passenger_template(
    template_id: int,
    payload: PassengerTemplateRequest,
    request: Request,
    passenger_service: PassengerTemplateService = Depends(get_passenger_template_service),
) -> dict:
    template = passenger_service.update_template(template_id, payload, request)
    return success_response(request, template.model_dump(by_alias=True, mode="json"))


@router.delete("/{template_id}", response_model=ApiSuccessDTO[dict])
def delete_passenger_template(
    template_id: int,
    request: Request,
    passenger_service: PassengerTemplateService = Depends(get_passenger_template_service),
) -> dict:
    return success_response(request, passenger_service.delete_template(template_id, request))
