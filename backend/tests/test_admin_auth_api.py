from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import create_app
from app.core.security import (
    hash_password,
    hash_secret,
    verify_password,
)
from app.repositories.auth import AdminConflictError, AdminUserRecord, SessionAdminRecord, get_auth_repository
import app.services.auth as auth_service_module
from app.services.auth import ADMIN_DUMMY_PASSWORD_HASH, InMemoryFailedLoginRateLimiter, get_admin_login_rate_limiter

from test_auth_api import FakeAuthRepository as VisitorFakeAuthRepository, csrf_headers


class FakeAuthRepository(VisitorFakeAuthRepository):
    def __init__(self):
        super().__init__()
        self.next_admin_id = 1
        self.admin_users: dict[int, AdminUserRecord] = {}
        self.admin_sessions: dict[str, SessionAdminRecord] = {}

    def find_admin_by_username(self, username: str) -> AdminUserRecord | None:
        return next((admin for admin in self.admin_users.values() if admin.username == username), None)

    def update_admin_profile(self, admin_user_id: int, username: str, password_hash: str) -> AdminUserRecord:
        admin = self.admin_users.get(admin_user_id)
        if admin is None or any(
            other.id != admin_user_id and other.username == username
            for other in self.admin_users.values()
        ):
            raise AdminConflictError
        next_admin = AdminUserRecord(
            id=admin.id,
            username=username,
            display_name=admin.display_name,
            password_hash=password_hash,
            role=admin.role,
            status=admin.status,
        )
        self.admin_users[admin.id] = next_admin
        return next_admin

    def create_admin_session(self, admin_user_id: int, session_token_hash: str, csrf_token_hash: str, expires_at: datetime) -> None:
        admin = self.admin_users[admin_user_id]
        self.admin_sessions[session_token_hash] = SessionAdminRecord(
            session_id=self.next_session_id,
            admin=admin,
            csrf_token_hash=csrf_token_hash,
            expires_at=expires_at,
            revoked_at=None,
        )
        self.next_session_id += 1

    def find_session_admin(self, session_token_hash: str, now: datetime) -> SessionAdminRecord | None:
        session = self.admin_sessions.get(session_token_hash)
        if session is None or session.revoked_at is not None or session.expires_at <= now:
            return None
        return SessionAdminRecord(
            session_id=session.session_id,
            admin=self.admin_users[session.admin.id],
            csrf_token_hash=session.csrf_token_hash,
            expires_at=session.expires_at,
            revoked_at=session.revoked_at,
        )

    def revoke_session(self, session_token_hash: str) -> None:
        super().revoke_session(session_token_hash)
        session = self.admin_sessions.get(session_token_hash)
        if session:
            self.admin_sessions[session_token_hash] = SessionAdminRecord(
                session_id=session.session_id,
                admin=session.admin,
                csrf_token_hash=session.csrf_token_hash,
                expires_at=session.expires_at,
                revoked_at=datetime.now(UTC),
            )

    def update_session_csrf(self, session_token_hash: str, csrf_token_hash: str, now: datetime) -> None:
        super().update_session_csrf(session_token_hash, csrf_token_hash, now)
        session = self.admin_sessions.get(session_token_hash)
        if session is None or session.revoked_at is not None or session.expires_at <= now:
            return
        self.admin_sessions[session_token_hash] = SessionAdminRecord(
            session_id=session.session_id,
            admin=session.admin,
            csrf_token_hash=csrf_token_hash,
            expires_at=session.expires_at,
            revoked_at=session.revoked_at,
        )


def build_client(
    repo: FakeAuthRepository,
    admin_login_rate_limiter: InMemoryFailedLoginRateLimiter | None = None,
    client_host: str = "testclient",
) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_repository] = lambda: repo
    if admin_login_rate_limiter is not None:
        app.dependency_overrides[get_admin_login_rate_limiter] = lambda: admin_login_rate_limiter
    return TestClient(app, client=(client_host, 50000))


def admin_login_payload(username: str = "admin", password: str = "AdminDemo!2026") -> dict:
    return {"username": username, "password": password}


def seed_enabled_admin(
    repo: FakeAuthRepository,
    password: str = "AdminDemo!2026",
    role: str = "SUPER_ADMIN",
) -> AdminUserRecord:
    admin = AdminUserRecord(
        id=repo.next_admin_id,
        username="admin",
        display_name="演示管理员",
        password_hash=hash_password(password, salt=bytes.fromhex("00112233445566778899aabbccddeeff")),
        role=role,
        status="ENABLED",
    )
    repo.next_admin_id += 1
    repo.admin_users[admin.id] = admin
    return admin


def test_admin_password_hash_uses_pbkdf2_format_and_constant_time_verification():
    password_hash = hash_password("AdminDemo!2026", salt=bytes.fromhex("00112233445566778899aabbccddeeff"))

    algorithm, iterations, salt_hex, hash_hex = password_hash.split("$")

    assert algorithm == "pbkdf2_sha256"
    assert iterations == "260000"
    assert len(bytes.fromhex(salt_hex)) == 16
    assert len(bytes.fromhex(hash_hex)) == 32
    assert verify_password("AdminDemo!2026", password_hash) is True
    assert verify_password("wrong-password", password_hash) is False
    assert verify_password("AdminDemo!2026", "pbkdf2_sha1$260000$00$00") is False
    assert verify_password("AdminDemo!2026", "not-a-valid-hash") is False


def test_admin_login_creates_admin_session_cookie_without_returning_sensitive_fields():
    repo = FakeAuthRepository()
    seed_enabled_admin(repo)
    client = build_client(repo)

    response = client.post(
        "/api/admin/auth/login",
        json=admin_login_payload(),
        headers=csrf_headers(client),
    )

    body = response.json()
    cookie = response.headers["set-cookie"]
    session_token = client.cookies.get("scenic_admin_session")
    assert response.status_code == 200
    assert body["data"] == {
        "adminUserId": 1,
        "username": "admin",
        "displayName": "演示管理员",
        "role": "SUPER_ADMIN",
    }
    response_text = response.text.lower()
    assert "password" not in response_text
    assert "session" not in response_text
    assert "csrf" not in response_text
    assert "scenic_admin_session=" in cookie
    assert "HttpOnly" in cookie
    assert session_token
    assert session_token not in repo.admin_sessions
    assert hash_secret(session_token) in repo.admin_sessions


def test_admin_login_rejects_extra_client_control_fields():
    repo = FakeAuthRepository()
    seed_enabled_admin(repo)
    client = build_client(repo)

    response = client.post(
        "/api/admin/auth/login",
        json=admin_login_payload() | {"adminUserId": 1, "sessionToken": "client-controlled"},
        headers=csrf_headers(client),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert "adminUserId" not in response.text
    assert "client-controlled" not in response.text


def test_admin_login_failures_use_same_error_for_missing_wrong_or_disabled_admin():
    repo = FakeAuthRepository()
    seed_enabled_admin(repo)
    disabled_admin = AdminUserRecord(
        id=repo.next_admin_id,
        username="disabled",
        display_name="禁用管理员",
        password_hash=hash_password("AdminDemo!2026", salt=bytes.fromhex("11112233445566778899aabbccddeeff")),
        role="OPERATOR",
        status="DISABLED",
    )
    repo.next_admin_id += 1
    repo.admin_users[disabled_admin.id] = disabled_admin
    client = build_client(repo)
    headers = csrf_headers(client)

    responses = [
        client.post("/api/admin/auth/login", json=admin_login_payload("missing"), headers=headers),
        client.post("/api/admin/auth/login", json=admin_login_payload(password="wrong-password"), headers=headers),
        client.post("/api/admin/auth/login", json=admin_login_payload("disabled"), headers=headers),
    ]

    for response in responses:
        assert response.status_code == 401
        assert response.json()["code"] == "ADMIN_LOGIN_FAILED"
        assert response.json()["message"] == "管理员账号或密码错误"
        assert "scenic_admin_session=" not in response.headers.get("set-cookie", "")
    assert repo.admin_sessions == {}


def test_admin_login_failures_verify_password_for_missing_wrong_and_disabled_admin(monkeypatch):
    repo = FakeAuthRepository()
    enabled_admin = seed_enabled_admin(repo)
    disabled_admin = AdminUserRecord(
        id=repo.next_admin_id,
        username="disabled",
        display_name="禁用管理员",
        password_hash=hash_password("AdminDemo!2026", salt=bytes.fromhex("11112233445566778899aabbccddeeff")),
        role="OPERATOR",
        status="DISABLED",
    )
    repo.next_admin_id += 1
    repo.admin_users[disabled_admin.id] = disabled_admin
    client = build_client(repo)
    headers = csrf_headers(client)
    checked_hashes = []

    def fake_verify_password(_password: str, expected_hash: str) -> bool:
        checked_hashes.append(expected_hash)
        return False

    monkeypatch.setattr(auth_service_module, "verify_password", fake_verify_password)

    responses = [
        client.post("/api/admin/auth/login", json=admin_login_payload("missing"), headers=headers),
        client.post("/api/admin/auth/login", json=admin_login_payload(password="wrong-password"), headers=headers),
        client.post("/api/admin/auth/login", json=admin_login_payload("disabled"), headers=headers),
    ]

    assert [response.status_code for response in responses] == [401, 401, 401]
    assert checked_hashes == [
        ADMIN_DUMMY_PASSWORD_HASH,
        enabled_admin.password_hash,
        ADMIN_DUMMY_PASSWORD_HASH,
    ]
    assert repo.admin_sessions == {}


def test_admin_login_requires_csrf():
    repo = FakeAuthRepository()
    seed_enabled_admin(repo)
    client = build_client(repo)

    response = client.post("/api/admin/auth/login", json=admin_login_payload())

    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_INVALID"
    assert repo.admin_sessions == {}


def test_admin_login_is_rate_limited_without_creating_session_or_consuming_csrf():
    repo = FakeAuthRepository()
    seed_enabled_admin(repo)
    current_time = [1000.0]
    limiter = InMemoryFailedLoginRateLimiter(
        max_attempts=2,
        window_seconds=60,
        clock=lambda: current_time[0],
    )
    client = build_client(repo, admin_login_rate_limiter=limiter, client_host="admin-limit")
    headers = csrf_headers(client)
    csrf_token = client.cookies.get("scenic_csrf")

    first = client.post("/api/admin/auth/login", json=admin_login_payload(password="bad-1"), headers=headers)
    second = client.post("/api/admin/auth/login", json=admin_login_payload(password="bad-2"), headers=headers)
    limited = client.post(
        "/api/admin/auth/login",
        json=admin_login_payload(password="bad-3"),
        headers=headers | {"x-request-id": "admin-rate-limited"},
    )

    assert first.status_code == 401
    assert second.status_code == 401
    assert limited.status_code == 429
    assert limited.json() == {
        "success": False,
        "code": "RATE_LIMITED",
        "message": "请求过于频繁，请稍后再试",
        "request_id": "admin-rate-limited",
    }
    assert client.cookies.get("scenic_csrf") == csrf_token
    assert "scenic_admin_session=" not in limited.headers.get("set-cookie", "")
    assert repo.admin_sessions == {}

    current_time[0] += 61
    retry = client.post("/api/admin/auth/login", json=admin_login_payload(), headers=headers)

    assert retry.status_code == 200
    assert client.cookies.get("scenic_csrf") == csrf_token
    assert repo.admin_sessions


def test_successful_admin_login_clears_previous_failure_counter():
    repo = FakeAuthRepository()
    seed_enabled_admin(repo)
    current_time = [1000.0]
    limiter = InMemoryFailedLoginRateLimiter(
        max_attempts=2,
        window_seconds=60,
        clock=lambda: current_time[0],
    )
    client = build_client(repo, admin_login_rate_limiter=limiter, client_host="admin-reset")
    headers = csrf_headers(client)

    failed = client.post("/api/admin/auth/login", json=admin_login_payload(password="bad"), headers=headers)
    success = client.post("/api/admin/auth/login", json=admin_login_payload(), headers=headers)
    client.cookies.clear()
    client.get("/api/auth/csrf")
    failed_after_success = client.post(
        "/api/admin/auth/login",
        json=admin_login_payload(password="bad-again"),
        headers=csrf_headers(client),
    )

    assert failed.status_code == 401
    assert success.status_code == 200
    assert failed_after_success.status_code == 401


def test_admin_me_requires_admin_session_and_ignores_visitor_session():
    repo = FakeAuthRepository()
    seed_enabled_admin(repo)
    client = build_client(repo)

    anonymous = client.get("/api/admin/auth/me")
    visitor_login = client.post(
        "/api/auth/visitor/register",
        json={"username": "demo_visitor", "password": "Visitor123", "phone": "13911112222"},
        headers=csrf_headers(client),
    )
    visitor_response = client.get("/api/admin/auth/me")

    assert visitor_login.status_code == 200
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"
    assert visitor_response.status_code == 401
    assert visitor_response.json()["code"] == "ADMIN_AUTH_REQUIRED"


def test_admin_session_survives_visitor_login_in_same_browser():
    repo = FakeAuthRepository()
    seed_enabled_admin(repo)
    client = build_client(repo)
    headers = csrf_headers(client)
    admin_login = client.post("/api/admin/auth/login", json=admin_login_payload(), headers=headers)
    admin_session_token = client.cookies.get("scenic_admin_session")

    visitor_login = client.post(
        "/api/auth/visitor/register",
        json={"username": "demo_visitor", "password": "Visitor123", "phone": "13911112222"},
        headers=headers,
    )
    visitor_session_token = client.cookies.get("scenic_session")
    admin_me = client.get("/api/admin/auth/me")
    visitor_me = client.get("/api/auth/me")

    assert admin_login.status_code == 200
    assert visitor_login.status_code == 200
    assert admin_session_token
    assert visitor_session_token
    assert client.cookies.get("scenic_admin_session") == admin_session_token
    assert admin_me.status_code == 200
    assert admin_me.json()["data"]["username"] == "admin"
    assert visitor_me.status_code == 200


def test_admin_me_returns_current_admin_and_touches_session():
    repo = FakeAuthRepository()
    seed_enabled_admin(repo)
    client = build_client(repo)
    login = client.post("/api/admin/auth/login", json=admin_login_payload(), headers=csrf_headers(client))

    response = client.get("/api/admin/auth/me")

    assert login.status_code == 200
    assert response.status_code == 200
    assert response.json()["data"]["username"] == "admin"
    assert repo.touched_sessions


def test_admin_can_update_own_username_and_password_with_current_password():
    repo = FakeAuthRepository()
    admin = seed_enabled_admin(repo)
    client = build_client(repo)
    headers = csrf_headers(client)
    login = client.post("/api/admin/auth/login", json=admin_login_payload(), headers=headers)

    response = client.patch(
        "/api/admin/auth/profile",
        json={"username": "ops_admin", "currentPassword": "AdminDemo!2026", "newPassword": "123456"},
        headers=headers,
    )

    body = response.json()
    next_admin = repo.admin_users[admin.id]
    assert login.status_code == 200
    assert response.status_code == 200
    assert body["data"] == {
        "adminUserId": admin.id,
        "username": "ops_admin",
        "displayName": "演示管理员",
        "role": "SUPER_ADMIN",
    }
    assert "password" not in response.text.lower()
    assert verify_password("123456", next_admin.password_hash)
    assert not verify_password("AdminDemo!2026", next_admin.password_hash)

    client.cookies.clear()
    new_login = client.post(
        "/api/admin/auth/login",
        json=admin_login_payload(username="ops_admin", password="123456"),
        headers=csrf_headers(client),
    )
    assert new_login.status_code == 200


def test_admin_profile_update_rejects_wrong_current_password():
    repo = FakeAuthRepository()
    admin = seed_enabled_admin(repo)
    client = build_client(repo)
    headers = csrf_headers(client)
    client.post("/api/admin/auth/login", json=admin_login_payload(), headers=headers)

    response = client.patch(
        "/api/admin/auth/profile",
        json={"username": "ops_admin", "currentPassword": "bad-password", "newPassword": "123456"},
        headers=headers,
    )

    assert response.status_code == 401
    assert response.json()["code"] == "ADMIN_PASSWORD_INVALID"
    assert repo.admin_users[admin.id].username == "admin"
    assert verify_password("AdminDemo!2026", repo.admin_users[admin.id].password_hash)


def test_admin_profile_update_requires_session_bound_csrf():
    repo = FakeAuthRepository()
    admin = seed_enabled_admin(repo)
    client = build_client(repo)
    headers = csrf_headers(client)
    login = client.post("/api/admin/auth/login", json=admin_login_payload(), headers=headers)
    client.cookies.set("scenic_csrf", "rotated-csrf")

    response = client.patch(
        "/api/admin/auth/profile",
        json={"username": "ops_admin", "currentPassword": "AdminDemo!2026", "newPassword": "123456"},
        headers={"x-csrf-token": "rotated-csrf"},
    )

    assert login.status_code == 200
    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_INVALID"
    assert repo.admin_users[admin.id].username == "admin"


def test_disabled_admin_existing_session_is_rejected_and_revoked():
    repo = FakeAuthRepository()
    admin = seed_enabled_admin(repo)
    client = build_client(repo)
    login = client.post("/api/admin/auth/login", json=admin_login_payload(), headers=csrf_headers(client))
    session_token = client.cookies.get("scenic_admin_session")
    repo.admin_users[admin.id] = AdminUserRecord(
        id=admin.id,
        username=admin.username,
        display_name=admin.display_name,
        password_hash=admin.password_hash,
        role=admin.role,
        status="DISABLED",
    )

    response = client.get("/api/admin/auth/me")

    assert login.status_code == 200
    assert response.status_code == 401
    assert response.json()["code"] == "ADMIN_AUTH_REQUIRED"
    assert repo.admin_sessions[hash_secret(session_token)].revoked_at is not None
    assert not repo.touched_sessions


def test_admin_session_is_not_accepted_by_visitor_me_endpoint():
    repo = FakeAuthRepository()
    seed_enabled_admin(repo)
    client = build_client(repo)
    login = client.post("/api/admin/auth/login", json=admin_login_payload(), headers=csrf_headers(client))
    session_token = client.cookies.get("scenic_admin_session")

    response = client.get("/api/auth/me")

    assert login.status_code == 200
    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"
    assert repo.admin_sessions[hash_secret(session_token)].revoked_at is None


def test_admin_logout_requires_csrf_and_session_bound_token():
    repo = FakeAuthRepository()
    seed_enabled_admin(repo)
    client = build_client(repo)
    headers = csrf_headers(client)
    login = client.post("/api/admin/auth/login", json=admin_login_payload(), headers=headers)
    session_token = client.cookies.get("scenic_admin_session")
    client.cookies.set("scenic_csrf", "rotated-csrf")

    missing_csrf = client.post("/api/admin/auth/logout")
    unbound_csrf = client.post("/api/admin/auth/logout", headers={"x-csrf-token": "rotated-csrf"})

    assert login.status_code == 200
    assert missing_csrf.status_code == 403
    assert missing_csrf.json()["code"] == "CSRF_INVALID"
    assert unbound_csrf.status_code == 403
    assert unbound_csrf.json()["code"] == "CSRF_INVALID"
    assert repo.admin_sessions[hash_secret(session_token)].revoked_at is None


def test_admin_logout_revokes_admin_session_and_clears_cookies():
    repo = FakeAuthRepository()
    seed_enabled_admin(repo)
    client = build_client(repo)
    headers = csrf_headers(client)
    client.post("/api/admin/auth/login", json=admin_login_payload(), headers=headers)
    session_token = client.cookies.get("scenic_admin_session")

    response = client.post("/api/admin/auth/logout", headers=headers)
    after_logout = client.get("/api/admin/auth/me")

    assert response.status_code == 200
    assert response.json()["data"] == {"loggedOut": True}
    assert repo.admin_sessions[hash_secret(session_token)].revoked_at is not None
    set_cookie = response.headers.get_list("set-cookie")
    assert any("scenic_admin_session=" in cookie and "Max-Age=0" in cookie for cookie in set_cookie)
    assert any("scenic_csrf=" in cookie and "Max-Age=0" in cookie for cookie in set_cookie)
    assert after_logout.status_code == 401
    assert after_logout.json()["code"] == "ADMIN_AUTH_REQUIRED"


def test_visitor_session_cannot_call_admin_logout_or_clear_visitor_session():
    repo = FakeAuthRepository()
    seed_enabled_admin(repo)
    client = build_client(repo)
    headers = csrf_headers(client)
    visitor_login = client.post("/api/auth/visitor/register", json={"username": "demo_visitor", "password": "Visitor123", "phone": "13911112222"}, headers=headers)
    visitor_session_token = client.cookies.get("scenic_session")

    response = client.post("/api/admin/auth/logout", headers=headers)
    me = client.get("/api/auth/me")

    assert visitor_login.status_code == 200
    assert response.status_code == 401
    assert response.json()["code"] == "ADMIN_AUTH_REQUIRED"
    assert repo.sessions[hash_secret(visitor_session_token)].revoked_at is None
    assert client.cookies.get("scenic_session") == visitor_session_token
    assert me.status_code == 200


def test_bind_csrf_to_current_session_updates_admin_session():
    repo = FakeAuthRepository()
    seed_enabled_admin(repo)
    client = build_client(repo)
    headers = csrf_headers(client)
    client.post("/api/admin/auth/login", json=admin_login_payload(), headers=headers)
    session_token = client.cookies.get("scenic_admin_session")
    old_hash = repo.admin_sessions[hash_secret(session_token)].csrf_token_hash

    new_csrf_response = client.get("/api/auth/csrf")
    new_csrf = client.cookies.get("scenic_csrf")

    assert new_csrf_response.status_code == 200
    assert repo.admin_sessions[hash_secret(session_token)].csrf_token_hash == hash_secret(new_csrf)
    assert repo.admin_sessions[hash_secret(session_token)].csrf_token_hash != old_hash


def test_postgres_admin_session_queries_filter_account_type_and_join_admin_user():
    from app.repositories.auth import PostgresAuthRepository

    captured = []

    class FakeConnection:
        def execute(self, sql, params=()):
            captured.append((sql, params))
            return self

        def fetchone(self):
            return None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    repository = PostgresAuthRepository()

    import app.repositories.auth as auth_repository_module

    original_connect_db = auth_repository_module.connect_db
    auth_repository_module.connect_db = lambda: FakeConnection()
    try:
        repository.find_session_admin("hashed-session", datetime.now(UTC))
    finally:
        auth_repository_module.connect_db = original_connect_db

    sql = captured[0][0]
    assert "JOIN admin_user a ON a.id = s.admin_user_id" in sql
    assert "s.account_type = 'ADMIN'" in sql
