#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
VENV_PYTHON = ROOT_DIR / ".venv" / "bin" / "python"
VENV_DIR = ROOT_DIR / ".venv"


WORKER_LOOP_ERROR = {
    "code": "ADMIN_EXPORT_WORKER_LOOP_FAILED",
    "message": "导出任务 worker 循环失败",
}


class WorkerArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError("invalid worker loop arguments")

    def exit(self, status: int = 0, message: str | None = None) -> None:
        raise ValueError("invalid worker loop arguments")


def maybe_reexec_with_venv(argv: list[str]) -> None:
    if VENV_PYTHON.exists() and Path(sys.prefix).resolve() != VENV_DIR.resolve():
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(Path(__file__).resolve()), *argv])


def ensure_backend_path() -> None:
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))


def load_runtime_dependencies() -> SimpleNamespace:
    ensure_backend_path()

    from app.core.config import get_settings
    from app.repositories.admin_exports import get_admin_export_job_repository
    from app.repositories.auth import get_auth_repository
    from app.repositories.orders import get_order_repository
    from app.services.admin_exports import (
        AdminExportJobService,
        AdminExportJobWorkerService,
        get_admin_export_file_storage,
    )
    from app.services.auth import AdminAuthService, InMemoryFailedLoginRateLimiter
    from app.services.orders import AdminCheckInService, AdminRefundService, AdminReportService

    return SimpleNamespace(
        get_settings=get_settings,
        get_admin_export_job_repository=get_admin_export_job_repository,
        get_auth_repository=get_auth_repository,
        get_order_repository=get_order_repository,
        AdminExportJobService=AdminExportJobService,
        AdminExportJobWorkerService=AdminExportJobWorkerService,
        get_admin_export_file_storage=get_admin_export_file_storage,
        AdminAuthService=AdminAuthService,
        InMemoryFailedLoginRateLimiter=InMemoryFailedLoginRateLimiter,
        AdminCheckInService=AdminCheckInService,
        AdminRefundService=AdminRefundService,
        AdminReportService=AdminReportService,
    )


def build_worker_service():
    deps = load_runtime_dependencies()

    get_settings = deps.get_settings
    get_admin_export_job_repository = deps.get_admin_export_job_repository
    get_auth_repository = deps.get_auth_repository
    get_order_repository = deps.get_order_repository
    AdminExportJobService = deps.AdminExportJobService
    AdminExportJobWorkerService = deps.AdminExportJobWorkerService
    get_admin_export_file_storage = deps.get_admin_export_file_storage
    AdminAuthService = deps.AdminAuthService
    InMemoryFailedLoginRateLimiter = deps.InMemoryFailedLoginRateLimiter
    AdminCheckInService = deps.AdminCheckInService
    AdminRefundService = deps.AdminRefundService
    AdminReportService = deps.AdminReportService

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


def public_export_job_payload(job) -> dict:
    payload = job.model_dump(by_alias=True, exclude_none=True, mode="json")
    filters = payload.get("filters")
    if isinstance(filters, dict):
        ensure_backend_path()
        from app.services.admin_exports import AdminExportJobService

        payload["filters"] = AdminExportJobService.redact_public_filters(filters)
    return payload


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = WorkerArgumentParser(add_help=False, description="Run the admin export worker loop.")
    parser.add_argument("--max-jobs", type=int, default=0)
    parser.add_argument("--max-idle-loops", type=int, default=0)
    parser.add_argument("--idle-sleep-seconds", type=float, default=5.0)
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> None:
    if args.max_jobs < 0:
        raise ValueError("max-jobs must not be negative")
    if args.max_idle_loops < 0:
        raise ValueError("max-idle-loops must not be negative")
    if not math.isfinite(args.idle_sleep_seconds) or args.idle_sleep_seconds < 0 or args.idle_sleep_seconds > 3600:
        raise ValueError("idle-sleep-seconds out of range")


def run_worker_loop(
    worker,
    *,
    max_jobs: int,
    max_idle_loops: int,
    idle_sleep_seconds: float,
) -> dict:
    processed = 0
    idle_loops = 0
    last_job = None

    while True:
        job = worker.process_next_pending_job()
        if job is not None:
            processed += 1
            idle_loops = 0
            last_job = public_export_job_payload(job)
            if max_jobs and processed >= max_jobs:
                break
            continue

        idle_loops += 1
        if max_idle_loops and idle_loops >= max_idle_loops:
            break
        time.sleep(idle_sleep_seconds)

    return {
        "running": False,
        "processed": processed,
        "idleLoops": idle_loops,
        "lastJob": last_job,
        "error": None,
    }


def error_payload() -> dict:
    return {
        "running": False,
        "processed": 0,
        "idleLoops": 0,
        "lastJob": None,
        "error": WORKER_LOOP_ERROR,
    }


def write_payload(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    try:
        raw_argv = sys.argv[1:] if argv is None else argv
        args = parse_args(raw_argv)
        validate_args(args)
        maybe_reexec_with_venv(raw_argv)
        payload = run_worker_loop(
            build_worker_service(),
            max_jobs=args.max_jobs,
            max_idle_loops=args.max_idle_loops,
            idle_sleep_seconds=args.idle_sleep_seconds,
        )
    except KeyboardInterrupt:
        payload = error_payload()
        write_payload(payload)
        return 130
    except Exception:
        payload = error_payload()
        write_payload(payload)
        return 1

    write_payload(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
