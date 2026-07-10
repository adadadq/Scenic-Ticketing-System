from fastapi import APIRouter, Depends, Request, Response

from app.core.responses import success_response
from app.core.security import require_double_submit_csrf
from app.schemas.admin_auth import AdminLoginRequest, AdminMeDTO, AdminProfileUpdateRequest
from app.schemas.auth import LogoutPayloadDTO
from app.schemas.common import ApiSuccessDTO
from app.services.auth import AdminAuthService, get_admin_auth_service

router = APIRouter(prefix="/api/admin/auth", tags=["admin-auth"])


@router.post("/login", response_model=ApiSuccessDTO[AdminMeDTO])
def login_admin(
    payload: AdminLoginRequest,
    request: Request,
    response: Response,
    admin_auth_service: AdminAuthService = Depends(get_admin_auth_service),
) -> dict:
    require_double_submit_csrf(request)
    admin = admin_auth_service.login_admin(payload, request, response)
    return success_response(request, admin.model_dump(by_alias=True, mode="json"))


@router.get("/me", response_model=ApiSuccessDTO[AdminMeDTO])
def get_admin_me(
    request: Request,
    admin_auth_service: AdminAuthService = Depends(get_admin_auth_service),
) -> dict:
    admin = admin_auth_service.current_admin(request)
    return success_response(request, admin.model_dump(by_alias=True, mode="json"))


@router.patch("/profile", response_model=ApiSuccessDTO[AdminMeDTO])
def update_admin_profile(
    payload: AdminProfileUpdateRequest,
    request: Request,
    response: Response,
    admin_auth_service: AdminAuthService = Depends(get_admin_auth_service),
) -> dict:
    admin = admin_auth_service.update_profile(payload, request, response)
    return success_response(request, admin.model_dump(by_alias=True, mode="json"))


@router.post("/logout", response_model=ApiSuccessDTO[LogoutPayloadDTO])
def logout_admin(
    request: Request,
    response: Response,
    admin_auth_service: AdminAuthService = Depends(get_admin_auth_service),
) -> dict:
    require_double_submit_csrf(request)
    admin_auth_service.logout_admin(request, response)
    return success_response(request, {"loggedOut": True})
