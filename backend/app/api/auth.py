from fastapi import APIRouter, Depends, Request, Response

from app.core.config import get_settings
from app.core.responses import success_response
from app.core.security import create_csrf_token_pair, require_double_submit_csrf, set_csrf_cookie
from app.schemas.auth import (
    CsrfPayloadDTO,
    LogoutPayloadDTO,
    VisitorLoginRequest,
    VisitorMeDTO,
    VisitorRegisterRequest,
)
from app.schemas.common import ApiSuccessDTO
from app.services.auth import AuthService, get_auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/csrf", response_model=ApiSuccessDTO[CsrfPayloadDTO])
async def get_csrf(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    token_pair = create_csrf_token_pair()
    set_csrf_cookie(response, token_pair.token)
    auth_service.bind_csrf_to_current_session(request, token_pair.token_hash)
    settings = get_settings()
    return success_response(
        request,
        {
            "headerName": settings.security.csrf_header_name,
        },
    )


@router.post("/visitor/login", response_model=ApiSuccessDTO[VisitorMeDTO])
def login_visitor(
    payload: VisitorLoginRequest,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    require_double_submit_csrf(request)
    visitor = auth_service.login_visitor(payload, request, response)
    return success_response(request, visitor.model_dump(by_alias=True, mode="json"))


@router.post("/visitor/register", response_model=ApiSuccessDTO[VisitorMeDTO])
def register_visitor(
    payload: VisitorRegisterRequest,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    require_double_submit_csrf(request)
    visitor = auth_service.register_visitor(payload, request, response)
    return success_response(request, visitor.model_dump(by_alias=True, mode="json"))


@router.get("/me", response_model=ApiSuccessDTO[VisitorMeDTO])
def get_me(request: Request, auth_service: AuthService = Depends(get_auth_service)) -> dict:
    visitor = auth_service.current_visitor(request)
    return success_response(request, visitor.model_dump(by_alias=True, mode="json"))


@router.post("/logout", response_model=ApiSuccessDTO[LogoutPayloadDTO])
def logout(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    require_double_submit_csrf(request)
    auth_service.logout(request, response)
    return success_response(request, {"loggedOut": True})
