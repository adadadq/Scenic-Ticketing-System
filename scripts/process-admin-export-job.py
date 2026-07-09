#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
VENV_PYTHON = ROOT_DIR / ".venv" / "bin" / "python"
VENV_DIR = ROOT_DIR / ".venv"

if VENV_PYTHON.exists() and Path(sys.prefix).resolve() != VENV_DIR.resolve():
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]])

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings  # noqa: E402
from app.repositories.admin_exports import get_admin_export_job_repository  # noqa: E402
from app.repositories.auth import get_auth_repository  # noqa: E402
from app.repositories.orders import get_order_repository  # noqa: E402
from app.services.admin_exports import (  # noqa: E402
    AdminExportJobService,
    AdminExportJobWorkerService,
    get_admin_export_file_storage,
)
from app.services.auth import AdminAuthService, InMemoryFailedLoginRateLimiter  # noqa: E402
from app.services.orders import AdminCheckInService, AdminRefundService, AdminReportService  # noqa: E402

WORKER_ERROR_PAYLOAD = {
    "processed": False,
    "job": None,
    "error": {
        "code": "ADMIN_EXPORT_JOB_WORKER_FAILED",
        "message": "导出任务处理失败",
    },
}


def public_export_job_payload(job) -> dict:
    payload = job.model_dump(by_alias=True, exclude_none=True, mode="json")
    filters = payload.get("filters")
    if isinstance(filters, dict):
        payload["filters"] = AdminExportJobService.redact_public_filters(filters)
    return payload


def build_worker_service() -> AdminExportJobWorkerService:
    settings = get_settings()
    auth_service = AdminAuthService(
        get_auth_repository(),
        InMemoryFailedLoginRateLimiter.from_settings(settings.security),
    )
    export_job_service = AdminExportJobService(get_admin_export_job_repository(), auth_service)
    order_repository = get_order_repository()
    report_service = AdminReportService(order_repository, auth_service)
    check_in_service = AdminCheckInService(order_repository, auth_service)
    refund_service = AdminRefundService(order_repository, auth_service)
    storage = get_admin_export_file_storage()
    return AdminExportJobWorkerService(export_job_service, report_service, check_in_service, refund_service, storage)


def main() -> int:
    try:
        processed_job = build_worker_service().process_next_pending_job()
    except Exception:
        sys.stdout.write(json.dumps(WORKER_ERROR_PAYLOAD, ensure_ascii=False, sort_keys=True))
        sys.stdout.write("\n")
        return 1

    payload = {
        "processed": processed_job is not None,
        "job": public_export_job_payload(processed_job) if processed_job else None,
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
