import logging
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

from app.core.config import SecuritySettings, get_settings
from app.core.errors import AppError, app_error_handler
from app.core.request_logging import REQUEST_LOGGER_NAME, UNSAFE_LOG_REQUEST_ID
from app.core.security import (
    clear_csrf_cookie,
    clear_session_cookie,
    create_csrf_token_pair,
    generate_token,
    hash_secret,
    require_double_submit_csrf,
    session_expires_at,
    set_csrf_cookie,
    set_session_cookie,
    verify_secret,
)
from app.main import create_app


def use_default_cors_settings(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    monkeypatch.delenv("CORS_ALLOWED_ORIGIN_REGEX", raising=False)


def test_generate_token_and_hash_are_not_plaintext():
    token = generate_token()
    token_hash = hash_secret(token)

    assert len(token) >= 32
    assert token not in token_hash
    assert verify_secret(token, token_hash) is True
    assert verify_secret("wrong-token", token_hash) is False


def test_create_csrf_token_pair_contains_hash_only_for_storage():
    token_pair = create_csrf_token_pair()

    assert token_pair.token
    assert token_pair.token_hash == hash_secret(token_pair.token)
    assert token_pair.token not in token_pair.token_hash


def test_session_expiry_uses_configured_ttl():
    settings = SecuritySettings(session_ttl_seconds=60)

    expires_at = session_expires_at(settings)

    delta = expires_at - datetime.now(UTC)
    assert 0 < delta.total_seconds() <= 60


def test_session_cookie_is_http_only():
    app = FastAPI()

    @app.get("/set-session")
    async def set_session(response: Response):
        set_session_cookie(
            response,
            "session-token",
            SecuritySettings(session_ttl_seconds=60, cookie_secure=True),
        )
        return {"ok": True}

    client = TestClient(app)

    response = client.get("/set-session")

    cookie = response.headers["set-cookie"]
    assert "scenic_session=session-token" in cookie
    assert "HttpOnly" in cookie
    assert "Max-Age=60" in cookie
    assert "Secure" in cookie
    assert "SameSite=lax" in cookie


def test_csrf_cookie_is_readable_by_frontend():
    app = FastAPI()

    @app.get("/set-csrf")
    async def set_csrf(response: Response):
        set_csrf_cookie(response, "csrf-token", SecuritySettings(session_ttl_seconds=60))
        return {"ok": True}

    client = TestClient(app)

    response = client.get("/set-csrf")

    cookie = response.headers["set-cookie"]
    assert "scenic_csrf=csrf-token" in cookie
    assert "HttpOnly" not in cookie
    assert "Max-Age=60" in cookie
    assert "SameSite=lax" in cookie


def test_clear_session_cookie_expires_cookie():
    app = FastAPI()

    @app.get("/clear-session")
    async def clear_session(response: Response):
        clear_session_cookie(response)
        return {"ok": True}

    client = TestClient(app)

    response = client.get("/clear-session")

    cookie = response.headers["set-cookie"]
    assert "scenic_session=" in cookie
    assert "Max-Age=0" in cookie
    assert "Path=/" in cookie


def test_clear_csrf_cookie_expires_cookie():
    app = FastAPI()

    @app.get("/clear-csrf")
    async def clear_csrf(response: Response):
        clear_csrf_cookie(response)
        return {"ok": True}

    client = TestClient(app)

    response = client.get("/clear-csrf")

    cookie = response.headers["set-cookie"]
    assert "scenic_csrf=" in cookie
    assert "Max-Age=0" in cookie
    assert "Path=/" in cookie


def test_double_submit_csrf_accepts_matching_header_and_cookie():
    app = FastAPI()

    @app.post("/mutate")
    async def mutate(request: Request):
        require_double_submit_csrf(request)
        return {"ok": True}

    client = TestClient(app)
    client.cookies.set("scenic_csrf", "csrf-token")

    response = client.post(
        "/mutate",
        headers={"x-csrf-token": "csrf-token"},
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    ("header_token", "cookie_token"),
    [
        ("csrf-token", "other-token"),
        ("csrf-token", None),
        (None, "csrf-token"),
    ],
)
def test_double_submit_csrf_rejects_missing_or_mismatched_token(header_token, cookie_token):
    app = FastAPI()
    app.add_exception_handler(AppError, app_error_handler)

    @app.post("/mutate")
    async def mutate(request: Request):
        require_double_submit_csrf(request)
        return {"ok": True}

    client = TestClient(app)
    if cookie_token:
        client.cookies.set("scenic_csrf", cookie_token)
    headers = {"x-csrf-token": header_token} if header_token else {}

    response = client.post(
        "/mutate",
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_INVALID"


def test_csrf_endpoint_sets_cookie_without_returning_token():
    client = TestClient(create_app())

    response = client.get("/api/auth/csrf", headers={"x-request-id": "csrf-request"})

    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["headerName"] == "x-csrf-token"
    assert "csrfToken" not in body["data"]
    assert body["request_id"] == "csrf-request"
    assert "scenic_csrf=" in response.headers["set-cookie"]
    assert "HttpOnly" not in response.headers["set-cookie"]


def test_custom_csrf_header_name_is_exposed_to_frontend_and_cors(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("CSRF_HEADER_NAME", "x-scenic-csrf")
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    monkeypatch.delenv("CORS_ALLOWED_ORIGIN_REGEX", raising=False)

    try:
        client = TestClient(create_app())

        csrf_response = client.get("/api/auth/csrf")
        preflight_response = client.options(
            "/api/orders",
            headers={
                "Origin": "http://localhost:54998",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,x-scenic-csrf,idempotency-key",
            },
        )

        assert csrf_response.status_code == 200
        assert csrf_response.json()["data"]["headerName"] == "x-scenic-csrf"
        assert preflight_response.status_code == 200
        assert "x-scenic-csrf" in preflight_response.headers["access-control-allow-headers"].lower()
    finally:
        get_settings.cache_clear()


def test_cors_allows_local_frontend_origin_with_credentials(monkeypatch):
    use_default_cors_settings(monkeypatch)
    client = TestClient(create_app())

    response = client.options(
        "/api/orders",
        headers={
            "Origin": "http://localhost:54998",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-csrf-token,idempotency-key",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:54998"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "DELETE" in response.headers["access-control-allow-methods"]
    assert "x-csrf-token" in response.headers["access-control-allow-headers"].lower()
    assert "idempotency-key" in response.headers["access-control-allow-headers"].lower()
    get_settings.cache_clear()


def test_cors_exposes_request_id_header_to_frontend(monkeypatch):
    use_default_cors_settings(monkeypatch)
    client = TestClient(create_app())

    response = client.get(
        "/api/health",
        headers={
            "Origin": "http://localhost:54998",
            "x-request-id": "cors-visible-request",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:54998"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert response.headers["x-request-id"] == "cors-visible-request"
    exposed_headers = response.headers["access-control-expose-headers"].lower()
    assert "x-request-id" in exposed_headers
    assert "content-disposition" in exposed_headers
    get_settings.cache_clear()


def test_cors_does_not_allow_external_origin_by_default(monkeypatch):
    use_default_cors_settings(monkeypatch)
    client = TestClient(create_app())

    response = client.options(
        "/api/orders",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-csrf-token",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
    get_settings.cache_clear()


def test_request_logging_omits_query_body_cookie_and_csrf(caplog):
    client = TestClient(create_app())
    caplog.set_level(logging.INFO, logger=REQUEST_LOGGER_NAME)
    client.cookies.set("scenic_session", "session-secret-value")
    client.cookies.set("scenic_csrf", "csrf-cookie-secret")

    response = client.post(
        "/api/auth/visitor/register?debug=Visitor123",
        json={
            "username": "zhangsan_001",
            "password": "Visitor123",
            "phone": "13911112222",
        },
        headers={
            "x-request-id": "safe-request-log",
            "x-csrf-token": "csrf-header-secret",
            "cookie": "manual-cookie-secret",
        },
    )

    request_logs = [record for record in caplog.records if record.name == REQUEST_LOGGER_NAME]
    assert response.status_code == 403
    assert len(request_logs) == 1
    log_record = request_logs[0]
    assert log_record.http_method == "POST"
    assert log_record.http_path == "/api/auth/visitor/register"
    assert log_record.http_status_code == 403
    assert log_record.request_id == "safe-request-log"
    assert isinstance(log_record.duration_ms, int | float)
    assert log_record.duration_ms >= 0

    logged_text = "\n".join(
        str(value)
        for record in request_logs
        for value in record.__dict__.values()
    )
    assert "debug=" not in logged_text
    assert "11010519491231002X" not in logged_text
    assert "13911112222" not in logged_text
    assert "session-secret-value" not in logged_text
    assert "csrf-cookie-secret" not in logged_text
    assert "csrf-header-secret" not in logged_text
    assert "manual-cookie-secret" not in logged_text


def test_request_logging_records_unhandled_errors_without_sensitive_detail(caplog):
    app = create_app()

    @app.get("/api/test/logging-boom")
    def logging_boom():
        raise RuntimeError("select id_number from visitor where csrf='raw-token'")

    client = TestClient(app, raise_server_exceptions=False)
    caplog.set_level(logging.INFO, logger=REQUEST_LOGGER_NAME)

    response = client.get(
        "/api/test/logging-boom?debug=11010519491231002X",
        headers={"x-request-id": "unhandled-log"},
    )

    request_logs = [record for record in caplog.records if record.name == REQUEST_LOGGER_NAME]
    assert response.status_code == 500
    assert len(request_logs) == 1
    log_record = request_logs[0]
    assert log_record.http_method == "GET"
    assert log_record.http_path == "/api/test/logging-boom"
    assert log_record.http_status_code == 500
    assert log_record.request_id == "unhandled-log"

    logged_text = "\n".join(
        str(value)
        for record in request_logs
        for value in record.__dict__.values()
    ).lower()
    for leaked_text in ("debug=", "11010519491231002x", "select", "id_number", "visitor", "csrf", "raw-token"):
        assert leaked_text not in logged_text


def test_request_logging_does_not_log_unsafe_client_request_id(caplog):
    client = TestClient(create_app())
    caplog.set_level(logging.INFO, logger=REQUEST_LOGGER_NAME)
    unsafe_request_id = "13911112222"

    response = client.get("/api/health", headers={"x-request-id": unsafe_request_id})

    request_logs = [record for record in caplog.records if record.name == REQUEST_LOGGER_NAME]
    assert response.status_code == 200
    assert response.headers["x-request-id"] == unsafe_request_id
    assert response.json()["request_id"] == unsafe_request_id
    assert len(request_logs) == 1
    assert request_logs[0].request_id == UNSAFE_LOG_REQUEST_ID
    logged_text = "\n".join(
        str(value)
        for record in request_logs
        for value in record.__dict__.values()
    )
    assert unsafe_request_id not in logged_text
