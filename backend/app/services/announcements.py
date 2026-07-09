from datetime import UTC, datetime
from threading import Lock

from fastapi import Request

from app.schemas.announcements import AnnouncementDTO, AnnouncementPublishRequest
from app.services.auth import AdminAuthService


class AnnouncementService:
    def __init__(self):
        self._lock = Lock()
        self._current = AnnouncementDTO(
            title="今日开放",
            content="遇龙河竹筏漂流正常开放，请按预约时段提前到达码头。",
            updated_at=datetime.now(UTC),
            operator_display_name="系统",
        )

    def current(self) -> AnnouncementDTO:
        with self._lock:
            return self._current

    def publish(self, payload: AnnouncementPublishRequest, request: Request, admin_auth_service: AdminAuthService) -> AnnouncementDTO:
        session = admin_auth_service.current_session_admin(request)
        notice = AnnouncementDTO(
            title=payload.title,
            content=payload.content,
            updated_at=datetime.now(UTC),
            operator_display_name=session.admin.display_name,
        )
        with self._lock:
            self._current = notice
        return notice


announcement_service = AnnouncementService()


def get_announcement_service() -> AnnouncementService:
    return announcement_service
