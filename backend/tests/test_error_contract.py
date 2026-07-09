from fastapi.testclient import TestClient

from app.main import create_app


ERROR_KEYS = {"success", "code", "message", "request_id"}


def assert_error_contract(response, *, status_code: int, code: str, request_id: str) -> None:
    body = response.json()

    assert response.status_code == status_code
    assert response.headers["x-request-id"] == request_id
    assert set(body) == ERROR_KEYS
    assert body["success"] is False
    assert body["code"] == code
    assert isinstance(body["message"], str)
    assert body["message"]
    assert body["request_id"] == request_id


def test_validation_error_uses_frontend_error_contract_without_raw_detail():
    client = TestClient(create_app())

    response = client.post(
        "/api/auth/visitor/login",
        headers={"x-request-id": "validation-contract"},
        json={
            "username": "bad user",
            "password": "short",
            "visitorId": 999,
        },
    )

    assert_error_contract(
        response,
        status_code=422,
        code="VALIDATION_ERROR",
        request_id="validation-contract",
    )
    body = response.json()
    assert body["message"] == "请求参数不合法"
    assert "detail" not in body
    assert "loc" not in response.text
    assert "bad user" not in response.text
    assert "visitorId" not in response.text


def test_app_error_uses_frontend_error_contract_for_csrf_failure():
    client = TestClient(create_app())

    response = client.post(
        "/api/auth/visitor/login",
        headers={"x-request-id": "csrf-contract"},
        json={"username": "zhangsan_001", "password": "Visitor123"},
    )

    assert_error_contract(
        response,
        status_code=403,
        code="CSRF_INVALID",
        request_id="csrf-contract",
    )


def test_error_contract_includes_generated_request_id_when_header_is_absent():
    client = TestClient(create_app())

    response = client.post(
        "/api/auth/visitor/login",
        json={"username": "zhangsan_001", "password": "Visitor123"},
    )
    body = response.json()

    assert response.status_code == 403
    assert set(body) == ERROR_KEYS
    assert body["success"] is False
    assert body["code"] == "CSRF_INVALID"
    assert response.headers["x-request-id"]
    assert body["request_id"] == response.headers["x-request-id"]


def test_unknown_route_uses_same_error_shape_as_business_errors():
    client = TestClient(create_app())

    response = client.get("/api/does-not-exist", headers={"x-request-id": "not-found-contract"})

    assert_error_contract(
        response,
        status_code=404,
        code="NOT_FOUND",
        request_id="not-found-contract",
    )


def test_unhandled_error_uses_generic_contract_without_sensitive_exception_detail():
    app = create_app()

    @app.get("/api/test/unhandled-error")
    def unhandled_error():
        raise RuntimeError(
            "select id_number from visitor where cookie='scenic_session' and csrf='raw-token'"
        )

    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/api/test/unhandled-error", headers={"x-request-id": "unhandled-contract"})

    assert_error_contract(
        response,
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        request_id="unhandled-contract",
    )
    assert response.json()["message"] == "服务暂时不可用"
    response_text = response.text.lower()
    for leaked_text in ("runtimeerror", "select", "id_number", "visitor", "cookie", "scenic_session", "csrf", "raw-token"):
        assert leaked_text not in response_text
