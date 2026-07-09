from fastapi import APIRouter, Depends, Request

from app.core.responses import success_response
from app.schemas.admin_settings import AdminSystemSettingsDTO, AdminSystemSettingsUpdateRequest
from app.schemas.common import ApiSuccessDTO
from app.services.admin_settings import AdminSystemSettingsService, get_admin_system_settings_service

router = APIRouter(prefix="/api/admin/settings", tags=["admin-settings"])


@router.get("", response_model=ApiSuccessDTO[AdminSystemSettingsDTO])
def get_admin_system_settings(
    request: Request,
    admin_system_settings_service: AdminSystemSettingsService = Depends(get_admin_system_settings_service),
) -> dict:
    settings = admin_system_settings_service.get_settings(request)
    return success_response(request, settings.model_dump(by_alias=True, mode="json"))


@router.patch("", response_model=ApiSuccessDTO[AdminSystemSettingsDTO])
def update_admin_system_settings(
    payload: AdminSystemSettingsUpdateRequest,
    request: Request,
    admin_system_settings_service: AdminSystemSettingsService = Depends(get_admin_system_settings_service),
) -> dict:
    settings = admin_system_settings_service.update_settings(payload, request)
    return success_response(request, settings.model_dump(by_alias=True, mode="json"))
