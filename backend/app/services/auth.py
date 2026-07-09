from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime
from threading import Lock

from fastapi import Depends, Request, Response

from app.core.config import SecuritySettings, get_settings
from app.core.errors import AppError
from app.core.security import (
    clear_csrf_cookie,
    clear_session_cookie,
    generate_token,
    get_csrf_cookie,
    get_csrf_header,
    hash_secret,
    hash_password,
    session_expires_at,
    set_session_cookie,
    verify_password,
    verify_secret,
)
from app.repositories.auth import AdminConflictError, AdminUserRecord, AuthRepository, VisitorConflictError, VisitorRecord, get_auth_repository
from app.schemas.admin_auth import AdminLoginRequest, AdminMeDTO, AdminProfileUpdateRequest
from app.schemas.auth import VisitorLoginRequest, VisitorMeDTO, VisitorRegisterRequest

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
ADMIN_DUMMY_PASSWORD_HASH = (
    "pbkdf2_sha256$260000$ffffffffffffffffffffffffffffffff$"
    "2f960db5683f42fb27778291f2815df78208fc9e09a987553407d74be75cafa6"
)


class InMemoryLoginRateLimiter:
    def __init__(
        self,
        max_attempts: int,
        window_seconds: int,
        clock: Callable[[], float] | None = None,
    ):
        self.max_attempts = max(1, max_attempts)
        self.window_seconds = max(1, window_seconds)
        self.clock = clock or time.monotonic
        self._attempts: dict[tuple[str, str], deque[float]] = {}
        self._lock = Lock()

    @classmethod
    def from_settings(cls, settings: SecuritySettings) -> InMemoryLoginRateLimiter:
        return cls(
            max_attempts=settings.login_rate_limit_max_attempts,
            window_seconds=settings.login_rate_limit_window_seconds,
        )

    def allow(self, client_host: str, phone: str) -> bool:
        now = self.clock()
        cutoff = now - self.window_seconds
        key = (client_host or "unknown", hash_secret(phone))
        with self._lock:
            attempts = self._attempts.setdefault(key, deque())
            while attempts and attempts[0] <= cutoff:
                attempts.popleft()
            if len(attempts) >= self.max_attempts:
                return False
            attempts.append(now)
            return True


class InMemoryFailedLoginRateLimiter:
    def __init__(
        self,
        max_attempts: int,
        window_seconds: int,
        clock: Callable[[], float] | None = None,
    ):
        self.max_attempts = max(1, max_attempts)
        self.window_seconds = max(1, window_seconds)
        self.clock = clock or time.monotonic
        self._failures: dict[tuple[str, str], deque[float]] = {}
        self._lock = Lock()

    @classmethod
    def from_settings(cls, settings: SecuritySettings) -> InMemoryFailedLoginRateLimiter:
        return cls(
            max_attempts=settings.login_rate_limit_max_attempts,
            window_seconds=settings.login_rate_limit_window_seconds,
        )

    def _key(self, client_host: str, username: str) -> tuple[str, str]:
        return (client_host or "unknown", hash_secret(username.strip().lower()))

    def allow(self, client_host: str, username: str) -> bool:
        now = self.clock()
        cutoff = now - self.window_seconds
        key = self._key(client_host, username)
        with self._lock:
            failures = self._failures.setdefault(key, deque())
            while failures and failures[0] <= cutoff:
                failures.popleft()
            return len(failures) < self.max_attempts

    def record_failure(self, client_host: str, username: str) -> None:
        now = self.clock()
        cutoff = now - self.window_seconds
        key = self._key(client_host, username)
        with self._lock:
            failures = self._failures.setdefault(key, deque())
            while failures and failures[0] <= cutoff:
                failures.popleft()
            failures.append(now)

    def clear(self, client_host: str, username: str) -> None:
        with self._lock:
            self._failures.pop(self._key(client_host, username), None)


class AuthService:
    def __init__(self, repository: AuthRepository, login_rate_limiter: InMemoryLoginRateLimiter):
        self.repository = repository
        self.login_rate_limiter = login_rate_limiter

    def login_visitor(self, payload: VisitorLoginRequest, request: Request, response: Response) -> VisitorMeDTO:
        client_host = request.client.host if request.client else "unknown"
        if not self.login_rate_limiter.allow(client_host, payload.username):
            raise AppError(429, "RATE_LIMITED", "请求过于频繁，请稍后再试")

        visitor = self.repository.find_visitor_by_username(payload.username)
        password_hash = (
            visitor.password_hash
            if visitor and visitor.visitor_scope == "REGISTERED" and visitor.password_hash
            else ADMIN_DUMMY_PASSWORD_HASH
        )
        if (
            visitor is None
            or visitor.visitor_scope != "REGISTERED"
            or not visitor.password_hash
            or not verify_password(payload.password, password_hash)
        ):
            raise AppError(401, "VISITOR_LOGIN_FAILED", "账号或密码错误")

        return self._start_session(visitor, request, response)

    def register_visitor(self, payload: VisitorRegisterRequest, request: Request, response: Response) -> VisitorMeDTO:
        existing_by_username = self.repository.find_visitor_by_username(payload.username)
        existing_by_phone = self.repository.find_visitor_by_phone(payload.phone)
        if existing_by_username or (existing_by_phone and existing_by_phone.visitor_scope == "REGISTERED"):
            raise AppError(409, "VISITOR_REGISTER_CONFLICT", "账号或手机号已被使用")

        try:
            password_hash = hash_password(payload.password)
            if existing_by_phone:
                visitor = self.repository.update_registered_account(
                    existing_by_phone.id,
                    payload.username,
                    password_hash,
                    payload.phone,
                )
            else:
                visitor = self.repository.create_registered_account(payload.username, password_hash, payload.phone)
        except VisitorConflictError as exc:
            raise AppError(409, "VISITOR_REGISTER_CONFLICT", "账号或手机号已被使用") from exc

        return self._start_session(visitor, request, response)

    def current_visitor(self, request: Request) -> VisitorMeDTO:
        session_record = self.current_session_visitor(request)
        self.repository.touch_session(session_record.session_id)
        return self.to_me_dto(session_record.visitor)

    def current_session_visitor(self, request: Request):
        session_token = request.cookies.get(get_settings().security.session_cookie_name, "")
        if not session_token:
            raise AppError(401, "AUTH_REQUIRED", "请先登录")

        session_record = self.repository.find_session_visitor(hash_secret(session_token), datetime.now(UTC))
        if session_record is None:
            raise AppError(401, "AUTH_REQUIRED", "请先登录")
        if request.method.upper() in MUTATING_METHODS:
            self.require_session_bound_csrf(request, session_record.csrf_token_hash)
        return session_record

    def logout(self, request: Request, response: Response) -> None:
        session_token = request.cookies.get(get_settings().security.session_cookie_name, "")
        if session_token:
            session_token_hash = hash_secret(session_token)
            session_record = self.repository.find_session_visitor(session_token_hash, datetime.now(UTC))
            if session_record is not None:
                self.require_session_bound_csrf(request, session_record.csrf_token_hash)
            self.repository.revoke_session(session_token_hash)
        clear_session_cookie(response)
        clear_csrf_cookie(response)

    def bind_csrf_to_current_session(self, request: Request, csrf_token_hash: str) -> None:
        settings = get_settings().security
        now = datetime.now(UTC)
        for cookie_name in (settings.session_cookie_name, settings.admin_session_cookie_name):
            session_token = request.cookies.get(cookie_name, "")
            if session_token:
                self.repository.update_session_csrf(
                    session_token_hash=hash_secret(session_token),
                    csrf_token_hash=csrf_token_hash,
                    now=now,
                )

    def require_registered_visitor(self, request: Request) -> VisitorRecord:
        session_record = self.current_session_visitor(request)
        if session_record.visitor.visitor_scope != "REGISTERED":
            raise AppError(403, "ACCOUNT_REQUIRED", "请先登录注册账号")
        return session_record.visitor

    def _start_session(self, visitor: VisitorRecord, request: Request, response: Response) -> VisitorMeDTO:
        session_token = generate_token()
        csrf_token = get_csrf_cookie(request)
        self.repository.create_session(
            visitor_id=visitor.id,
            session_token_hash=hash_secret(session_token),
            csrf_token_hash=hash_secret(csrf_token),
            expires_at=session_expires_at(),
        )
        set_session_cookie(response, session_token)
        return self.to_me_dto(visitor)

    @staticmethod
    def require_session_bound_csrf(request: Request, csrf_token_hash: str) -> None:
        csrf_token = get_csrf_header(request)
        if not verify_secret(csrf_token, csrf_token_hash):
            raise AppError(403, "CSRF_INVALID", "CSRF 校验失败")

    @staticmethod
    def to_me_dto(visitor: VisitorRecord) -> VisitorMeDTO:
        return VisitorMeDTO(
            visitor_id=visitor.id,
            visitor_name=visitor.visitor_name,
            phone=visitor.phone,
            visitor_scope=visitor.visitor_scope,
            is_registered=visitor.visitor_scope == "REGISTERED",
        )


class AdminAuthService:
    def __init__(self, repository: AuthRepository, login_rate_limiter: InMemoryFailedLoginRateLimiter):
        self.repository = repository
        self.login_rate_limiter = login_rate_limiter

    def login_admin(self, payload: AdminLoginRequest, request: Request, response: Response) -> AdminMeDTO:
        client_host = request.client.host if request.client else "unknown"
        if not self.login_rate_limiter.allow(client_host, payload.username):
            raise AppError(429, "RATE_LIMITED", "请求过于频繁，请稍后再试")

        admin = self.repository.find_admin_by_username(payload.username)
        password_hash = admin.password_hash if admin is not None and admin.status == "ENABLED" else ADMIN_DUMMY_PASSWORD_HASH
        password_ok = verify_password(payload.password, password_hash)
        if admin is None or admin.status != "ENABLED" or not password_ok:
            self.login_rate_limiter.record_failure(client_host, payload.username)
            raise AppError(401, "ADMIN_LOGIN_FAILED", "管理员账号或密码错误")

        self.login_rate_limiter.clear(client_host, payload.username)
        session_token = generate_token()
        csrf_token = get_csrf_cookie(request)
        self.repository.create_admin_session(
            admin_user_id=admin.id,
            session_token_hash=hash_secret(session_token),
            csrf_token_hash=hash_secret(csrf_token),
            expires_at=session_expires_at(),
        )
        set_session_cookie(response, session_token, cookie_name=get_settings().security.admin_session_cookie_name)
        return self.to_admin_dto(admin)

    def current_admin(self, request: Request) -> AdminMeDTO:
        session_record = self.current_session_admin(request)
        self.repository.touch_session(session_record.session_id)
        return self.to_admin_dto(session_record.admin)

    def current_session_admin(self, request: Request):
        session_token = request.cookies.get(get_settings().security.admin_session_cookie_name, "")
        if not session_token:
            raise AppError(401, "ADMIN_AUTH_REQUIRED", "请先登录管理员账号")

        session_token_hash = hash_secret(session_token)
        now = datetime.now(UTC)
        session_record = self.repository.find_session_admin(session_token_hash, now)
        if session_record is None:
            visitor_session = self.repository.find_session_visitor(session_token_hash, now)
            if visitor_session is not None:
                raise AppError(403, "ADMIN_FORBIDDEN", "当前账号无后台权限")
            raise AppError(401, "ADMIN_AUTH_REQUIRED", "请先登录管理员账号")
        if session_record.admin.status != "ENABLED":
            self.repository.revoke_session(session_token_hash)
            raise AppError(401, "ADMIN_AUTH_REQUIRED", "请先登录管理员账号")
        if request.method.upper() in MUTATING_METHODS:
            AuthService.require_session_bound_csrf(request, session_record.csrf_token_hash)
        return session_record

    def require_super_admin(self, request: Request):
        session_record = self.current_session_admin(request)
        if session_record.admin.role != "SUPER_ADMIN":
            raise AppError(403, "ADMIN_FORBIDDEN", "当前账号无后台权限")
        return session_record

    def update_profile(self, payload: AdminProfileUpdateRequest, request: Request) -> AdminMeDTO:
        session_record = self.current_session_admin(request)
        admin = session_record.admin
        if not verify_password(payload.current_password, admin.password_hash):
            raise AppError(401, "ADMIN_PASSWORD_INVALID", "当前密码错误")

        password_hash = hash_password(payload.new_password) if payload.new_password else admin.password_hash
        try:
            next_admin = self.repository.update_admin_profile(admin.id, payload.username, password_hash)
        except AdminConflictError as exc:
            raise AppError(409, "ADMIN_USERNAME_CONFLICT", "管理员账号已被使用") from exc
        return self.to_admin_dto(next_admin)

    def logout_admin(self, request: Request, response: Response) -> None:
        session_record = self.current_session_admin(request)
        self.repository.revoke_session(hash_secret(request.cookies.get(get_settings().security.admin_session_cookie_name, "")))
        clear_session_cookie(response, cookie_name=get_settings().security.admin_session_cookie_name)
        clear_csrf_cookie(response)
        self.repository.touch_session(session_record.session_id)

    @staticmethod
    def to_admin_dto(admin: AdminUserRecord) -> AdminMeDTO:
        return AdminMeDTO(
            admin_user_id=admin.id,
            username=admin.username,
            display_name=admin.display_name,
            role=admin.role,
        )


def get_login_rate_limiter(request: Request) -> InMemoryLoginRateLimiter:
    return request.app.state.login_rate_limiter


def get_admin_login_rate_limiter(request: Request) -> InMemoryFailedLoginRateLimiter:
    return request.app.state.admin_login_rate_limiter


def get_auth_service(
    repository: AuthRepository = Depends(get_auth_repository),
    login_rate_limiter: InMemoryLoginRateLimiter = Depends(get_login_rate_limiter),
) -> AuthService:
    return AuthService(repository, login_rate_limiter)


def get_admin_auth_service(
    repository: AuthRepository = Depends(get_auth_repository),
    login_rate_limiter: InMemoryFailedLoginRateLimiter = Depends(get_admin_login_rate_limiter),
) -> AdminAuthService:
    return AdminAuthService(repository, login_rate_limiter)
