from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import create_app
from app.core.security import hash_secret
from app.repositories.auth import get_auth_repository
from app.repositories.admin_settings import AdminSystemSettingLogRecord, get_admin_system_settings_repository

from test_admin_auth_api import FakeAuthRepository, admin_login_payload, seed_enabled_admin
from test_auth_api import csrf_headers


class FakeAdminSystemSettingsRepository:
    def __init__(self):
        self.values: dict[str, str] = {}
        self.logs: list[AdminSystemSettingLogRecord] = []
        self.last_audit_context: dict | None = None

    def get_settings(self):
        return self.values.copy(), None

    def update_settings(
        self,
        values,
        *,
        admin_user_id,
        operator_username,
        operator_display_name,
        request_id,
        source_ip,
        device_id,
        admin_session_id,
        user_agent,
        action,
        changed_keys,
    ):
        self.values.update(values)
        self.last_audit_context = {
            "source_ip": source_ip,
            "device_id": device_id,
            "admin_session_id": admin_session_id,
            "user_agent": user_agent,
        }
        self.logs.insert(
            0,
            AdminSystemSettingLogRecord(
                created_at=datetime.now(UTC),
                operator_display_name=operator_display_name,
                operator_username=operator_username,
                action=action,
                source_ip=source_ip,
            ),
        )
        return self.values.copy(), None

    def list_recent_logs(self, limit: int):
        return self.logs[:limit]


def build_client(auth_repo: FakeAuthRepository, settings_repo: FakeAdminSystemSettingsRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repo
    app.dependency_overrides[get_admin_system_settings_repository] = lambda: settings_repo
    return TestClient(app, client=("203.0.113.77", 50000))


def test_admin_can_update_basic_system_settings_and_get_audit_log():
    auth_repo = FakeAuthRepository()
    settings_repo = FakeAdminSystemSettingsRepository()
    seed_enabled_admin(auth_repo)
    client = build_client(auth_repo, settings_repo)
    headers = csrf_headers(client)

    assert client.post("/api/admin/auth/login", json=admin_login_payload(), headers=headers).status_code == 200

    response = client.patch(
        "/api/admin/settings",
        json={"scenicName": "遇龙河新版景区", "serviceTimeStart": "09:00", "perOrderLimit": 12},
        headers=headers,
    )

    data = response.json()["data"]
    assert response.status_code == 200
    assert data["scenicName"] == "遇龙河新版景区"
    assert data["serviceTimeStart"] == "09:00"
    assert data["perOrderLimit"] == 12
    assert data["recentLogs"][0]["operatorUsername"] == "admin"
    assert data["recentLogs"][0]["action"] == "修改了系统配置：景区名称等 3 项"
    assert settings_repo.last_audit_context == {
        "source_ip": "203.0.113.77",
        "device_id": hash_secret(client.cookies.get("scenic_admin_device"))[:24],
        "admin_session_id": 1,
        "user_agent": "testclient",
    }


def test_operator_cannot_update_system_settings():
    auth_repo = FakeAuthRepository()
    settings_repo = FakeAdminSystemSettingsRepository()
    seed_enabled_admin(auth_repo, role="OPERATOR")
    client = build_client(auth_repo, settings_repo)
    headers = csrf_headers(client)
    assert client.post("/api/admin/auth/login", json=admin_login_payload(), headers=headers).status_code == 200

    response = client.patch("/api/admin/settings", json={"perOrderLimit": 12}, headers=headers)

    assert response.status_code == 403
    assert response.json()["code"] == "ADMIN_FORBIDDEN"
    assert settings_repo.values == {}


def test_admin_settings_rejects_invalid_time_range():
    auth_repo = FakeAuthRepository()
    settings_repo = FakeAdminSystemSettingsRepository()
    seed_enabled_admin(auth_repo)
    client = build_client(auth_repo, settings_repo)
    headers = csrf_headers(client)
    assert client.post("/api/admin/auth/login", json=admin_login_payload(), headers=headers).status_code == 200

    response = client.patch(
        "/api/admin/settings",
        json={"ticketTimeStart": "18:00", "ticketTimeEnd": "08:00"},
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ADMIN_SETTINGS_INVALID"
