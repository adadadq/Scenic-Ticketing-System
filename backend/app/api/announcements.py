from fastapi import APIRouter, Depends, Request

from app.core.responses import success_response
from app.schemas.announcements import AnnouncementDTO, AnnouncementPublishRequest
from app.schemas.common import ApiSuccessDTO
from app.services.announcements import AnnouncementService, get_announcement_service
from app.services.auth import AdminAuthService, get_admin_auth_service

router = APIRouter(tags=["announcements"])


@router.get("/api/announcements/current", response_model=ApiSuccessDTO[AnnouncementDTO])
def get_current_announcement(
    request: Request,
    announcement_service: AnnouncementService = Depends(get_announcement_service),
) -> dict:
    notice = announcement_service.current()
    return success_response(request, notice.model_dump(by_alias=True, mode="json"))


@router.post("/api/admin/announcements/current", response_model=ApiSuccessDTO[AnnouncementDTO])
def publish_current_announcement(
    payload: AnnouncementPublishRequest,
    request: Request,
    announcement_service: AnnouncementService = Depends(get_announcement_service),
    admin_auth_service: AdminAuthService = Depends(get_admin_auth_service),
) -> dict:
    notice = announcement_service.publish(payload, request, admin_auth_service)
    return success_response(request, notice.model_dump(by_alias=True, mode="json"))
