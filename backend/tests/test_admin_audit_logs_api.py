from datetime import UTC, datetime

from fastapi.testclient import TestClient

import app.api.admin_audit_logs as audit_api
from app.main import create_app
from app.repositories.auth import get_auth_repository

from test_admin_auth_api import FakeAuthRepository, admin_login_payload, seed_enabled_admin
from test_auth_api import csrf_headers


class FakeResult:
    def __init__(self, *, row=None, rows=None):
        self.row = row
        self.rows = rows or []

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class FakeAuditConnection:
    def __init__(self):
        self.queries: list[str] = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, _params=()):
        self.queries.append(sql)
        if "CAST(SUM(row_count)" in sql:
            return FakeResult(row={"total": 1})
        return FakeResult(
            rows=[
                {
                    "id": "TICKET-1",
                    "created_at": datetime(2026, 7, 10, 12, 0, tzinfo=UTC),
                    "operator_display_name": "演示管理员",
                    "operator_username": "admin",
                    "type": "票种管理",
                    "object": "成人票",
                    "result": "成功",
                    "action": "修改票种",
                    "request_id": "req-1",
                    "source_ip": "203.0.113.88",
                    "device_id": "0123456789abcdef01234567",
                    "admin_session_id": 7,
                    "user_agent": "AdminBrowser/1.0",
                }
            ]
        )


def test_unified_admin_audit_api_returns_device_source_context(monkeypatch):
    auth_repo = FakeAuthRepository()
    seed_enabled_admin(auth_repo)
    connection = FakeAuditConnection()
    monkeypatch.setattr(audit_api, "connect_db", lambda: connection)
    app = create_app()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repo
    client = TestClient(app)
    assert client.post(
        "/api/admin/auth/login",
        json=admin_login_payload(),
        headers=csrf_headers(client),
    ).status_code == 200

    response = client.get("/api/admin/audit-logs")

    assert response.status_code == 200
    assert response.json()["data"]["items"][0] == {
        "id": "TICKET-1",
        "createdAt": "2026-07-10T12:00:00Z",
        "operatorDisplayName": "演示管理员",
        "operatorUsername": "admin",
        "type": "票种管理",
        "object": "成人票",
        "result": "成功",
        "action": "修改票种",
        "requestId": "req-1",
        "sourceIp": "203.0.113.88",
        "deviceId": "0123456789abcdef01234567",
        "adminSessionId": 7,
        "userAgent": "AdminBrowser/1.0",
    }
    assert "admin_ticket_audit_log" in "\n".join(connection.queries)
