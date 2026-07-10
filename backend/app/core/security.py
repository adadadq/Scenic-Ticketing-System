from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import Request, Response

from app.core.config import SecuritySettings, get_settings
from app.core.errors import AppError


TOKEN_BYTES = 32
ADMIN_DEVICE_COOKIE_NAME = "scenic_admin_device"
ADMIN_DEVICE_COOKIE_MAX_AGE = 365 * 24 * 60 * 60
ADMIN_DEVICE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")
PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 260000
PASSWORD_SALT_BYTES = 16
PASSWORD_HASH_BYTES = 32


@dataclass(frozen=True)
class CsrfTokenPair:
    token: str
    token_hash: str


def generate_token() -> str:
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def verify_secret(secret: str, expected_hash: str) -> bool:
    if not secret or not expected_hash:
        return False
    return hmac.compare_digest(hash_secret(secret), expected_hash)


def hash_password(password: str, salt: bytes | None = None) -> str:
    password_salt = salt or secrets.token_bytes(PASSWORD_SALT_BYTES)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        password_salt,
        PASSWORD_HASH_ITERATIONS,
        dklen=PASSWORD_HASH_BYTES,
    )
    return (
        f"{PASSWORD_HASH_ALGORITHM}$"
        f"{PASSWORD_HASH_ITERATIONS}$"
        f"{password_salt.hex()}$"
        f"{password_hash.hex()}"
    )


def verify_password(password: str, expected_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_hex, hash_hex = expected_hash.split("$")
        iterations = int(iterations_text)
        salt = bytes.fromhex(salt_hex)
        stored_hash = bytes.fromhex(hash_hex)
    except (ValueError, TypeError):
        return False

    if (
        algorithm != PASSWORD_HASH_ALGORITHM
        or iterations != PASSWORD_HASH_ITERATIONS
        or len(salt) != PASSWORD_SALT_BYTES
        or len(stored_hash) != PASSWORD_HASH_BYTES
    ):
        return False

    candidate_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
        dklen=PASSWORD_HASH_BYTES,
    )
    return hmac.compare_digest(candidate_hash, stored_hash)


def create_csrf_token_pair() -> CsrfTokenPair:
    token = generate_token()
    return CsrfTokenPair(token=token, token_hash=hash_secret(token))


def session_expires_at(settings: SecuritySettings | None = None) -> datetime:
    security_settings = settings or get_settings().security
    return datetime.now(UTC) + timedelta(seconds=security_settings.session_ttl_seconds)


def set_session_cookie(
    response: Response,
    session_token: str,
    settings: SecuritySettings | None = None,
    cookie_name: str | None = None,
) -> None:
    security_settings = settings or get_settings().security
    response.set_cookie(
        key=cookie_name or security_settings.session_cookie_name,
        value=session_token,
        max_age=security_settings.session_ttl_seconds,
        httponly=True,
        secure=security_settings.cookie_secure,
        samesite=security_settings.cookie_samesite,
        path="/",
    )


def ensure_admin_device_cookie(request: Request, response: Response) -> str:
    token = request.cookies.get(ADMIN_DEVICE_COOKIE_NAME, "").strip()
    if not ADMIN_DEVICE_TOKEN_RE.fullmatch(token):
        token = generate_token()
        settings = get_settings().security
        response.set_cookie(
            key=ADMIN_DEVICE_COOKIE_NAME,
            value=token,
            max_age=ADMIN_DEVICE_COOKIE_MAX_AGE,
            httponly=True,
            secure=settings.cookie_secure,
            samesite="lax",
            path="/",
        )
    return token


def get_admin_device_id(request: Request) -> str | None:
    token = request.cookies.get(ADMIN_DEVICE_COOKIE_NAME, "").strip()
    if not ADMIN_DEVICE_TOKEN_RE.fullmatch(token):
        return None
    return hash_secret(token)[:24]


def clear_session_cookie(
    response: Response,
    settings: SecuritySettings | None = None,
    cookie_name: str | None = None,
) -> None:
    security_settings = settings or get_settings().security
    response.delete_cookie(key=cookie_name or security_settings.session_cookie_name, path="/")


def clear_csrf_cookie(response: Response, settings: SecuritySettings | None = None) -> None:
    security_settings = settings or get_settings().security
    response.delete_cookie(key=security_settings.csrf_cookie_name, path="/")


def set_csrf_cookie(response: Response, csrf_token: str, settings: SecuritySettings | None = None) -> None:
    security_settings = settings or get_settings().security
    response.set_cookie(
        key=security_settings.csrf_cookie_name,
        value=csrf_token,
        max_age=security_settings.session_ttl_seconds,
        httponly=False,
        secure=security_settings.cookie_secure,
        samesite=security_settings.cookie_samesite,
        path="/",
    )


def get_csrf_header(request: Request, settings: SecuritySettings | None = None) -> str:
    security_settings = settings or get_settings().security
    return request.headers.get(security_settings.csrf_header_name, "").strip()


def get_csrf_cookie(request: Request, settings: SecuritySettings | None = None) -> str:
    security_settings = settings or get_settings().security
    return request.cookies.get(security_settings.csrf_cookie_name, "").strip()


def require_double_submit_csrf(request: Request, settings: SecuritySettings | None = None) -> None:
    header_token = get_csrf_header(request, settings)
    cookie_token = get_csrf_cookie(request, settings)
    if not header_token or not cookie_token or not hmac.compare_digest(header_token, cookie_token):
        raise AppError(403, "CSRF_INVALID", "CSRF 校验失败")
