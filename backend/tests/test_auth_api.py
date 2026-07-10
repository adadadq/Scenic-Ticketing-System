from datetime import UTC, datetime, timedelta

from fastapi import Depends, Request
from fastapi.testclient import TestClient

from app.core.security import hash_password, hash_secret
from app.main import create_app
from app.repositories.auth import SessionVisitorRecord, VisitorConflictError, VisitorRecord, get_auth_repository
from app.services.auth import AuthService, InMemoryLoginRateLimiter, get_auth_service, get_login_rate_limiter


class FakeAuthRepository:
    def __init__(self):
        self.next_visitor_id = 1
        self.next_session_id = 1
        self.visitors: dict[int, VisitorRecord] = {}
        self.sessions: dict[str, SessionVisitorRecord] = {}
        self.touched_sessions: list[int] = []

    def find_visitor_by_phone(self, phone: str) -> VisitorRecord | None:
        return next((visitor for visitor in self.visitors.values() if visitor.phone == phone), None)

    def find_visitor_by_username(self, username: str) -> VisitorRecord | None:
        return next((visitor for visitor in self.visitors.values() if visitor.username == username), None)

    def find_visitor_by_id_doc(self, id_type: str, id_number: str) -> VisitorRecord | None:
        return next(
            (
                visitor
                for visitor in self.visitors.values()
                if visitor.id_type == id_type and visitor.id_number == id_number
            ),
            None,
        )

    def create_temp_visitor(self, phone: str) -> VisitorRecord:
        if self.find_visitor_by_phone(phone) or self.find_visitor_by_id_doc("TEMP_PHONE", phone):
            raise VisitorConflictError
        visitor = VisitorRecord(
            id=self.next_visitor_id,
            visitor_name=f"临时游客{phone[-4:]}",
            id_type="TEMP_PHONE",
            id_number=phone,
            phone=phone,
            visitor_scope="TEMP",
        )
        self.next_visitor_id += 1
        self.visitors[visitor.id] = visitor
        return visitor

    def get_or_create_temp_visitor(self, phone: str) -> VisitorRecord:
        visitor = self.find_visitor_by_phone(phone)
        if visitor:
            return visitor
        return self.create_temp_visitor(phone)

    def create_registered_visitor(self, visitor_name: str, id_type: str, id_number: str, phone: str) -> VisitorRecord:
        if self.find_visitor_by_phone(phone) or self.find_visitor_by_id_doc(id_type, id_number):
            raise VisitorConflictError
        visitor = VisitorRecord(
            id=self.next_visitor_id,
            visitor_name=visitor_name,
            id_type=id_type,
            id_number=id_number,
            phone=phone,
            visitor_scope="REGISTERED",
        )
        self.next_visitor_id += 1
        self.visitors[visitor.id] = visitor
        return visitor

    def create_registered_account(self, username: str, password_hash: str, phone: str) -> VisitorRecord:
        if self.find_visitor_by_username(username) or self.find_visitor_by_phone(phone):
            raise VisitorConflictError
        visitor = VisitorRecord(
            id=self.next_visitor_id,
            visitor_name=username,
            id_type="ACCOUNT",
            id_number=f"ACCOUNT:{username}",
            phone=phone,
            visitor_scope="REGISTERED",
            username=username,
            password_hash=password_hash,
        )
        self.next_visitor_id += 1
        self.visitors[visitor.id] = visitor
        return visitor

    def update_registered_account(self, visitor_id: int, username: str, password_hash: str, phone: str) -> VisitorRecord:
        current = self.visitors.get(visitor_id)
        username_owner = self.find_visitor_by_username(username)
        phone_owner = self.find_visitor_by_phone(phone)
        if (
            not current
            or current.visitor_scope != "TEMP"
            or (username_owner and username_owner.id != visitor_id)
            or (phone_owner and phone_owner.id != visitor_id)
        ):
            raise VisitorConflictError
        visitor = VisitorRecord(
            id=visitor_id,
            visitor_name=username,
            id_type="ACCOUNT",
            id_number=f"ACCOUNT:{username}",
            phone=phone,
            visitor_scope="REGISTERED",
            username=username,
            password_hash=password_hash,
        )
        self.visitors[visitor.id] = visitor
        return visitor

    def update_registered_visitor(self, visitor_id: int, visitor_name: str, id_type: str, id_number: str, phone: str) -> VisitorRecord:
        current = self.visitors.get(visitor_id)
        phone_owner = self.find_visitor_by_phone(phone)
        doc_owner = self.find_visitor_by_id_doc(id_type, id_number)
        can_update_identity = current and (
            current.visitor_scope == "TEMP"
            or (current.visitor_scope == "REGISTERED" and current.id_type == id_type and current.id_number == id_number)
        )
        if (
            not can_update_identity
            or (phone_owner and phone_owner.id != visitor_id)
            or (doc_owner and doc_owner.id != visitor_id)
        ):
            raise VisitorConflictError
        visitor = VisitorRecord(
            id=visitor_id,
            visitor_name=visitor_name,
            id_type=id_type,
            id_number=id_number,
            phone=phone,
            visitor_scope="REGISTERED",
        )
        self.visitors[visitor.id] = visitor
        return visitor

    def create_session(self, visitor_id: int, session_token_hash: str, csrf_token_hash: str, expires_at: datetime) -> None:
        visitor = self.visitors[visitor_id]
        self.sessions[session_token_hash] = SessionVisitorRecord(
            session_id=self.next_session_id,
            visitor=visitor,
            csrf_token_hash=csrf_token_hash,
            expires_at=expires_at,
            revoked_at=None,
        )
        self.next_session_id += 1

    def find_session_visitor(self, session_token_hash: str, now: datetime) -> SessionVisitorRecord | None:
        session = self.sessions.get(session_token_hash)
        if session is None or session.revoked_at is not None or session.expires_at <= now:
            return None
        return SessionVisitorRecord(
            session_id=session.session_id,
            visitor=self.visitors[session.visitor.id],
            csrf_token_hash=session.csrf_token_hash,
            expires_at=session.expires_at,
            revoked_at=session.revoked_at,
        )

    def revoke_session(self, session_token_hash: str) -> None:
        session = self.sessions.get(session_token_hash)
        if session:
            self.sessions[session_token_hash] = SessionVisitorRecord(
                session_id=session.session_id,
                visitor=session.visitor,
                csrf_token_hash=session.csrf_token_hash,
                expires_at=session.expires_at,
                revoked_at=datetime.now(UTC),
            )

    def update_session_csrf(self, session_token_hash: str, csrf_token_hash: str, now: datetime) -> None:
        session = self.sessions.get(session_token_hash)
        if session is None or session.revoked_at is not None or session.expires_at <= now:
            return
        self.sessions[session_token_hash] = SessionVisitorRecord(
            session_id=session.session_id,
            visitor=session.visitor,
            csrf_token_hash=csrf_token_hash,
            expires_at=session.expires_at,
            revoked_at=session.revoked_at,
        )

    def touch_session(self, session_id: int) -> None:
        self.touched_sessions.append(session_id)


def build_client(
    repo: FakeAuthRepository,
    login_rate_limiter: InMemoryLoginRateLimiter | None = None,
    client_host: str = "testclient",
) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_repository] = lambda: repo
    if login_rate_limiter is not None:
        app.dependency_overrides[get_login_rate_limiter] = lambda: login_rate_limiter
    return TestClient(app, client=(client_host, 50000))


def csrf_headers(client: TestClient) -> dict[str, str]:
    response = client.get("/api/auth/csrf")
    assert response.status_code == 200
    token = client.cookies.get("scenic_csrf")
    assert token
    return {"x-csrf-token": token}


def valid_register_payload(phone: str = "13911112222") -> dict:
    return {
        "username": "zhangsan_001",
        "password": "Visitor123",
        "phone": phone,
    }


def valid_login_payload(username: str = "zhangsan_001", password: str = "Visitor123") -> dict:
    return {"username": username, "password": password}


def seed_registered_account(
    repo: FakeAuthRepository,
    username: str = "zhangsan_001",
    password: str = "Visitor123",
    phone: str = "13911112222",
) -> VisitorRecord:
    return repo.create_registered_account(username, hash_password(password), phone)


def test_me_requires_login():
    client = build_client(FakeAuthRepository())

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"


def test_visitor_login_creates_registered_session_cookie_without_returning_token():
    repo = FakeAuthRepository()
    seed_registered_account(repo)
    client = build_client(repo)

    response = client.post(
        "/api/auth/visitor/login",
        json=valid_login_payload(),
        headers=csrf_headers(client),
    )

    body = response.json()
    cookie = response.headers["set-cookie"]
    session_token = client.cookies.get("scenic_session")
    assert response.status_code == 200
    assert body["data"]["visitorScope"] == "REGISTERED"
    assert body["data"]["isRegistered"] is True
    assert "session" not in str(body["data"]).lower()
    assert "scenic_session=" in cookie
    assert "HttpOnly" in cookie
    assert session_token
    assert session_token not in repo.sessions
    assert hash_secret(session_token) in repo.sessions


def test_visitor_login_is_rate_limited_per_client_and_username():
    repo = FakeAuthRepository()
    seed_registered_account(repo)
    seed_registered_account(repo, "lisi_001", "Visitor123", "13811112222")
    current_time = [1000.0]
    limiter = InMemoryLoginRateLimiter(
        max_attempts=2,
        window_seconds=60,
        clock=lambda: current_time[0],
    )
    client = build_client(repo, limiter)
    headers = csrf_headers(client)

    first_response = client.post("/api/auth/visitor/login", json=valid_login_payload(), headers=headers)
    second_response = client.post("/api/auth/visitor/login", json=valid_login_payload(), headers=headers)
    session_count_before_limited = len(repo.sessions)
    limited_response = client.post(
        "/api/auth/visitor/login",
        json=valid_login_payload(),
        headers=headers | {"x-request-id": "login-rate-limit"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert len(repo.sessions) == session_count_before_limited
    assert limited_response.status_code == 429
    assert "scenic_session=" not in limited_response.headers.get("set-cookie", "")
    assert limited_response.headers["x-request-id"] == "login-rate-limit"
    assert limited_response.json() == {
        "success": False,
        "code": "RATE_LIMITED",
        "message": "请求过于频繁，请稍后再试",
        "request_id": "login-rate-limit",
    }
    assert "Visitor123" not in limited_response.text
    assert len(repo.sessions) == session_count_before_limited

    other_phone_response = client.post("/api/auth/visitor/login", json=valid_login_payload("lisi_001"), headers=headers)
    current_time[0] += 61
    after_window_response = client.post("/api/auth/visitor/login", json=valid_login_payload(), headers=headers)

    assert other_phone_response.status_code == 200
    assert after_window_response.status_code == 200


def test_rate_limited_first_login_does_not_create_visitor_session_or_cookie():
    repo = FakeAuthRepository()
    client_host = "198.51.100.31"
    current_time = [1000.0]
    limiter = InMemoryLoginRateLimiter(
        max_attempts=1,
        window_seconds=60,
        clock=lambda: current_time[0],
    )
    client = build_client(repo, limiter, client_host=client_host)
    headers = csrf_headers(client)
    assert limiter.allow(client_host, "zhangsan_001") is True

    response = client.post(
        "/api/auth/visitor/login",
        json=valid_login_payload(),
        headers=headers | {"x-request-id": "first-login-rate-limit"},
    )

    assert response.status_code == 429
    assert response.json() == {
        "success": False,
        "code": "RATE_LIMITED",
        "message": "请求过于频繁，请稍后再试",
        "request_id": "first-login-rate-limit",
    }
    assert repo.visitors == {}
    assert repo.sessions == {}
    assert client.cookies.get("scenic_session") is None
    assert "scenic_session=" not in response.headers.get("set-cookie", "")


def test_rate_limited_first_login_can_retry_after_window_with_same_csrf():
    repo = FakeAuthRepository()
    seed_registered_account(repo)
    client_host = "198.51.100.32"
    current_time = [1000.0]
    limiter = InMemoryLoginRateLimiter(
        max_attempts=1,
        window_seconds=60,
        clock=lambda: current_time[0],
    )
    client = build_client(repo, limiter, client_host=client_host)
    headers = csrf_headers(client)
    csrf_token = client.cookies.get("scenic_csrf")
    assert csrf_token
    assert limiter.allow(client_host, "zhangsan_001") is True

    limited_response = client.post(
        "/api/auth/visitor/login",
        json=valid_login_payload(),
        headers=headers | {"x-request-id": "retry-rate-limit"},
    )
    assert limited_response.status_code == 429
    assert repo.sessions == {}
    assert client.cookies.get("scenic_csrf") == csrf_token

    current_time[0] += 61
    retry_response = client.post(
        "/api/auth/visitor/login",
        json=valid_login_payload(),
        headers=headers | {"x-request-id": "retry-after-rate-limit"},
    )

    assert client.cookies.get("scenic_csrf") == csrf_token
    assert retry_response.status_code == 200
    assert retry_response.json()["data"]["visitorScope"] == "REGISTERED"
    session_token = client.cookies.get("scenic_session")
    assert session_token
    session = repo.sessions[hash_secret(session_token)]
    assert session.csrf_token_hash == hash_secret(csrf_token)


def test_login_requires_csrf():
    client = build_client(FakeAuthRepository())

    response = client.post("/api/auth/visitor/login", json=valid_login_payload())

    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_INVALID"


def test_visitor_login_rejects_phone_only_payload():
    repo = FakeAuthRepository()
    seed_registered_account(repo, phone="13911112222")
    client = build_client(repo)

    response = client.post(
        "/api/auth/visitor/login",
        json={"phone": "13911112222"},
        headers=csrf_headers(client),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert repo.sessions == {}


def test_visitor_login_with_missing_password_hash_fails_without_session():
    repo = FakeAuthRepository()
    visitor = VisitorRecord(
        id=repo.next_visitor_id,
        visitor_name="broken_account",
        id_type="ACCOUNT",
        id_number="ACCOUNT:broken_account",
        phone="13911112222",
        visitor_scope="REGISTERED",
        username="broken_account",
        password_hash=None,
    )
    repo.next_visitor_id += 1
    repo.visitors[visitor.id] = visitor
    client = build_client(repo)

    response = client.post(
        "/api/auth/visitor/login",
        json=valid_login_payload("broken_account"),
        headers=csrf_headers(client),
    )

    assert response.status_code == 401
    assert response.json()["code"] == "VISITOR_LOGIN_FAILED"
    assert repo.sessions == {}


def test_register_requires_csrf():
    client = build_client(FakeAuthRepository())

    response = client.post("/api/auth/visitor/register", json=valid_register_payload())

    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_INVALID"


def test_visitor_register_rejects_legacy_identity_payload():
    client = build_client(FakeAuthRepository())

    response = client.post(
        "/api/auth/visitor/register",
        json={
            "visitorName": "张三",
            "idType": "ID_CARD",
            "idNumber": "11010519491231002X",
            "phone": "13911112222",
        },
        headers=csrf_headers(client),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_logout_requires_csrf():
    repo = FakeAuthRepository()
    seed_registered_account(repo)
    client = build_client(repo)
    headers = csrf_headers(client)
    client.post("/api/auth/visitor/login", json=valid_login_payload(), headers=headers)

    response = client.post("/api/auth/logout")

    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_INVALID"


def test_logout_rejects_csrf_token_not_bound_to_session():
    repo = FakeAuthRepository()
    seed_registered_account(repo)
    client = build_client(repo)
    headers = csrf_headers(client)
    client.post("/api/auth/visitor/login", json=valid_login_payload(), headers=headers)
    session_token = client.cookies.get("scenic_session")
    client.cookies.set("scenic_csrf", "rotated-csrf")

    response = client.post("/api/auth/logout", headers={"x-csrf-token": "rotated-csrf"})

    session = repo.sessions[hash_secret(session_token)]
    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_INVALID"
    assert session.revoked_at is None


def test_csrf_endpoint_rebinds_new_token_to_current_session():
    repo = FakeAuthRepository()
    seed_registered_account(repo)
    client = build_client(repo)
    headers = csrf_headers(client)
    client.post("/api/auth/visitor/login", json=valid_login_payload(), headers=headers)

    refreshed_headers = csrf_headers(client)
    response = client.post("/api/auth/logout", headers=refreshed_headers)

    assert response.status_code == 200
    assert response.json()["data"] == {"loggedOut": True}


def test_register_creates_registered_account_and_me_uses_session():
    repo = FakeAuthRepository()
    client = build_client(repo)
    headers = csrf_headers(client)

    register_response = client.post(
        "/api/auth/visitor/register",
        json=valid_register_payload(),
        headers=headers,
    )
    me_response = client.get("/api/auth/me")

    assert register_response.status_code == 200
    assert register_response.json()["data"]["visitorScope"] == "REGISTERED"
    assert register_response.json()["data"]["isRegistered"] is True
    assert me_response.status_code == 200
    assert me_response.json()["data"]["visitorName"] == "zhangsan_001"
    assert me_response.json()["data"]["visitorScope"] == "REGISTERED"
    assert repo.touched_sessions


def test_registered_phone_cannot_be_reused_by_new_account():
    repo = FakeAuthRepository()
    seed_registered_account(repo, "lisi_001", "Visitor123", "13911112222")
    client = build_client(repo)

    response = client.post(
        "/api/auth/visitor/register",
        json=valid_register_payload(),
        headers=csrf_headers(client),
    )

    visitor = repo.find_visitor_by_phone("13911112222")
    assert response.status_code == 409
    assert response.json()["code"] == "VISITOR_REGISTER_CONFLICT"
    assert visitor.username == "lisi_001"
    assert visitor.visitor_name == "lisi_001"


def test_register_conflicts_when_username_exists():
    repo = FakeAuthRepository()
    seed_registered_account(repo, "zhangsan_001", "Visitor123", "13811112222")
    client = build_client(repo)

    response = client.post(
        "/api/auth/visitor/register",
        json=valid_register_payload(),
        headers=csrf_headers(client),
    )

    assert response.status_code == 409
    assert response.json()["code"] == "VISITOR_REGISTER_CONFLICT"


def test_temp_visitor_cannot_use_registered_guard():
    repo = FakeAuthRepository()
    app = create_app()
    app.dependency_overrides[get_auth_repository] = lambda: repo

    @app.get("/test/registered-only")
    def registered_only(request: Request, auth_service: AuthService = Depends(get_auth_service)):
        visitor = auth_service.require_registered_visitor(request)
        return {"visitorId": visitor.id}

    visitor = repo.create_temp_visitor("13911112222")
    session_token = "temp-session-token"
    repo.sessions[hash_secret(session_token)] = SessionVisitorRecord(
        session_id=1,
        visitor=visitor,
        csrf_token_hash=hash_secret("csrf-token"),
        expires_at=datetime.now(UTC) + timedelta(seconds=60),
        revoked_at=None,
    )
    client = TestClient(app)
    client.cookies.set("scenic_session", session_token)

    response = client.get("/test/registered-only")

    assert response.status_code == 403
    assert response.json()["code"] == "ACCOUNT_REQUIRED"


def test_auth_dto_rejects_invalid_account_and_phone():
    client = build_client(FakeAuthRepository())
    headers = csrf_headers(client)

    login_response = client.post("/api/auth/visitor/login", json={"username": "x", "password": "short"}, headers=headers)
    register_response = client.post(
        "/api/auth/visitor/register",
        json={"username": "zhangsan_001", "password": "Visitor123", "phone": "123"},
        headers=headers,
    )

    assert login_response.status_code == 422
    assert register_response.status_code == 422


def test_auth_requests_reject_extra_client_controlled_fields_without_echoing_them():
    client = build_client(FakeAuthRepository())
    headers = csrf_headers(client)

    login_response = client.post(
        "/api/auth/visitor/login",
        json=valid_login_payload() | {"visitorId": 999},
        headers=headers,
    )
    register_response = client.post(
        "/api/auth/visitor/register",
        json=valid_register_payload() | {"sessionToken": "client-controlled"},
        headers=headers,
    )

    assert login_response.status_code == 422
    login_body_without_request_id = login_response.json() | {"request_id": ""}
    assert login_body_without_request_id["code"] == "VALIDATION_ERROR"
    assert "visitorId" not in str(login_body_without_request_id)
    assert "999" not in str(login_body_without_request_id)
    assert register_response.status_code == 422
    register_body_without_request_id = register_response.json() | {"request_id": ""}
    assert register_body_without_request_id["code"] == "VALIDATION_ERROR"
    assert "sessionToken" not in str(register_body_without_request_id)
    assert "client-controlled" not in str(register_body_without_request_id)


def test_logout_revokes_session_and_clears_cookie():
    repo = FakeAuthRepository()
    seed_registered_account(repo)
    client = build_client(repo)
    headers = csrf_headers(client)
    client.post("/api/auth/visitor/login", json=valid_login_payload(), headers=headers)

    response = client.post("/api/auth/logout", headers=headers)
    me_response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["data"] == {"loggedOut": True}
    set_cookie_headers = response.headers.get_list("set-cookie")
    session_cookie = next(cookie for cookie in set_cookie_headers if cookie.startswith("scenic_session="))
    csrf_cookie = next(cookie for cookie in set_cookie_headers if cookie.startswith("scenic_csrf="))
    assert "Max-Age=0" in session_cookie
    assert "Max-Age=0" in csrf_cookie
    assert me_response.status_code == 401


def test_login_can_refresh_csrf_after_logout_cookie_cleanup():
    repo = FakeAuthRepository()
    seed_registered_account(repo)
    seed_registered_account(repo, "lisi_001", "Visitor123", "13811112222")
    client = build_client(repo)
    headers = csrf_headers(client)
    client.post("/api/auth/visitor/login", json=valid_login_payload(), headers=headers)
    client.post("/api/auth/logout", headers=headers)

    refreshed_headers = csrf_headers(client)
    response = client.post(
        "/api/auth/visitor/login",
        json=valid_login_payload("lisi_001"),
        headers=refreshed_headers,
    )

    assert response.status_code == 200
    assert response.json()["data"]["phone"] == "13811112222"
    assert client.cookies.get("scenic_session")


def test_expired_session_requires_login():
    repo = FakeAuthRepository()
    visitor = repo.create_temp_visitor("13911112222")
    session_token = "expired-session-token"
    repo.sessions[hash_secret(session_token)] = SessionVisitorRecord(
        session_id=1,
        visitor=visitor,
        csrf_token_hash=hash_secret("csrf-token"),
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
        revoked_at=None,
    )
    client = build_client(repo)
    client.cookies.set("scenic_session", session_token)

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"
