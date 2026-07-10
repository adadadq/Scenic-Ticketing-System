from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.core.security import hash_secret
from app.main import create_app
from app.repositories.admin_tickets import AdminTicketRecord, get_admin_tickets_repository
from app.repositories.auth import get_auth_repository

from test_admin_auth_api import FakeAuthRepository, admin_login_payload, seed_enabled_admin
from test_auth_api import csrf_headers


class FakeAdminTicketsRepository:
    def __init__(self):
        self.audit = None

    def list_tickets(self):
        return []

    def save_ticket(self, ticket_id, *, audit, **_values):
        self.audit = audit
        return AdminTicketRecord(
            id=ticket_id or 1,
            name="成人票",
            type="ADULT",
            route="遇龙河",
            sale_price=Decimal("128.00"),
            stock=10,
            allocated_quota=10,
            status="ON_SALE",
            description=None,
            date_from=date(2026, 7, 10),
            date_to=date(2026, 7, 10),
            slot_quota=10,
            slot_quotas=(("08:30", "10:30", 10),),
        )

    def delete_ticket(self, ticket_id, audit):
        self.audit = audit


def test_ticket_write_captures_device_ip_session_and_user_agent():
    auth_repo = FakeAuthRepository()
    tickets_repo = FakeAdminTicketsRepository()
    seed_enabled_admin(auth_repo)
    app = create_app()
    app.dependency_overrides[get_auth_repository] = lambda: auth_repo
    app.dependency_overrides[get_admin_tickets_repository] = lambda: tickets_repo
    client = TestClient(app, client=("203.0.113.88", 50000))
    headers = csrf_headers(client)
    assert client.post("/api/admin/auth/login", json=admin_login_payload(), headers=headers).status_code == 200

    response = client.post(
        "/api/admin/tickets",
        headers={**headers, "user-agent": "AdminBrowser/1.0"},
        json={
            "name": "成人票",
            "type": "ADULT",
            "route": "遇龙河",
            "salePrice": "128.00",
            "stock": 10,
            "status": "ON_SALE",
            "dateFrom": "2026-07-10",
            "dateTo": "2026-07-10",
            "slotQuota": 10,
            "slotQuotas": [{"slotStartTime": "08:30", "slotEndTime": "10:30", "quota": 10}],
        },
    )

    assert response.status_code == 200
    assert tickets_repo.audit.source_ip == "203.0.113.88"
    assert tickets_repo.audit.device_id == hash_secret(client.cookies.get("scenic_admin_device"))[:24]
    assert tickets_repo.audit.admin_session_id == 1
    assert tickets_repo.audit.user_agent == "AdminBrowser/1.0"
