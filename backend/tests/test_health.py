from fastapi.testclient import TestClient

from app.api import health as health_module
from app.api.health import get_database_connection
from app.main import create_app


class FakeCursor:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class FakeHealthConnection:
    def __init__(self, row=None, error: Exception | None = None):
        self.row = {"ok": 1} if row is None else row
        self.error = error
        self.closed = False

    def execute(self, query, params=None):
        if self.error:
            raise self.error
        assert query == "SELECT 1 AS ok"
        assert params is None
        return FakeCursor(self.row)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        self.closed = True


def test_health_returns_contract_response():
    client = TestClient(create_app())

    response = client.get("/api/health", headers={"x-request-id": "test-request-id"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "test-request-id"
    assert response.json() == {
        "success": True,
        "data": {
            "status": "ok",
            "service": "scenic-ticket-api",
            "environment": "development",
        },
        "request_id": "test-request-id",
    }


def test_database_health_returns_ok_when_database_ping_succeeds():
    connection = FakeHealthConnection()
    app = create_app()
    app.dependency_overrides[get_database_connection] = lambda: connection
    client = TestClient(app)

    response = client.get("/api/health/db", headers={"x-request-id": "db-health-request-id"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "db-health-request-id"
    assert response.json() == {
        "success": True,
        "data": {
            "status": "ok",
            "database": "ok",
            "service": "scenic-ticket-api",
            "environment": "development",
        },
        "request_id": "db-health-request-id",
    }


def test_database_health_closes_connection_from_real_dependency(monkeypatch):
    connection = FakeHealthConnection()
    monkeypatch.setattr(health_module, "connect_db", lambda: connection)
    client = TestClient(create_app())

    response = client.get("/api/health/db")

    assert response.status_code == 200
    assert connection.closed is True


def test_database_health_returns_503_when_ping_returns_false():
    app = create_app()
    app.dependency_overrides[get_database_connection] = lambda: FakeHealthConnection(row={"ok": 0})
    client = TestClient(app)

    response = client.get("/api/health/db", headers={"x-request-id": "db-down-request-id"})

    assert response.status_code == 503
    assert response.headers["x-request-id"] == "db-down-request-id"
    assert response.json() == {
        "success": False,
        "code": "DATABASE_UNAVAILABLE",
        "message": "数据库暂时不可用",
        "request_id": "db-down-request-id",
    }


def test_database_health_returns_503_when_connection_fails(monkeypatch):
    def fail_connect():
        raise RuntimeError("password=secret host=db.internal")

    monkeypatch.setattr(health_module, "connect_db", fail_connect)
    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.get("/api/health/db", headers={"x-request-id": "db-connect-error"})

    assert response.status_code == 503
    assert response.headers["x-request-id"] == "db-connect-error"
    assert response.json() == {
        "success": False,
        "code": "DATABASE_UNAVAILABLE",
        "message": "数据库暂时不可用",
        "request_id": "db-connect-error",
    }
    assert "secret" not in response.text
    assert "db.internal" not in response.text


def test_database_health_hides_connection_errors():
    app = create_app()
    app.dependency_overrides[get_database_connection] = lambda: FakeHealthConnection(
        error=RuntimeError("password=secret host=db.internal")
    )
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/api/health/db", headers={"x-request-id": "db-error-request-id"})

    assert response.status_code == 503
    assert response.json()["code"] == "DATABASE_UNAVAILABLE"
    assert "secret" not in response.text
    assert "db.internal" not in response.text


def test_unknown_route_uses_error_contract():
    client = TestClient(create_app())

    response = client.get("/api/missing", headers={"x-request-id": "missing-request-id"})

    assert response.status_code == 404
    assert response.headers["x-request-id"] == "missing-request-id"
    assert response.json() == {
        "success": False,
        "code": "NOT_FOUND",
        "message": "资源不存在",
        "request_id": "missing-request-id",
    }


def test_unhandled_error_uses_safe_error_contract():
    app = create_app()

    @app.get("/api/boom")
    async def boom():
        raise RuntimeError("database password leaked in stack")

    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/api/boom", headers={"x-request-id": "boom-request-id"})

    assert response.status_code == 500
    assert response.headers["x-request-id"] == "boom-request-id"
    assert response.json() == {
        "success": False,
        "code": "INTERNAL_SERVER_ERROR",
        "message": "服务暂时不可用",
        "request_id": "boom-request-id",
    }
    assert "database password" not in response.text
    assert "Traceback" not in response.text
