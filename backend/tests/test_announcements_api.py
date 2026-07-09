from fastapi.testclient import TestClient

from app.main import create_app
from app.repositories.auth import get_auth_repository

from test_admin_auth_api import FakeAuthRepository, admin_login_payload, seed_enabled_admin
from test_auth_api import csrf_headers


def build_client(auth_repo: FakeAuthRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repo
    return TestClient(app)


def test_admin_can_publish_current_announcement_and_visitors_can_read_it():
    auth_repo = FakeAuthRepository()
    seed_enabled_admin(auth_repo)
    client = build_client(auth_repo)
    headers = csrf_headers(client)

    assert client.post("/api/admin/auth/login", json=admin_login_payload(), headers=headers).status_code == 200

    response = client.post(
        "/api/admin/announcements/current",
        json={"title": "临时调整", "content": "今日 15:30 后场次请提前 20 分钟到码头。"},
        headers=headers,
    )

    data = response.json()["data"]
    assert response.status_code == 200
    assert data["title"] == "临时调整"
    assert data["operatorDisplayName"] == "演示管理员"

    public_response = client.get("/api/announcements/current")

    assert public_response.status_code == 200
    assert public_response.json()["data"]["content"] == "今日 15:30 后场次请提前 20 分钟到码头。"
