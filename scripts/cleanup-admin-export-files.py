#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
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
from app.services.admin_exports import AdminExportFileStorage, AdminExportJobService, get_admin_export_file_storage  # noqa: E402
from app.services.auth import AdminAuthService, InMemoryFailedLoginRateLimiter  # noqa: E402


CLEANUP_ERROR_PAYLOAD = {
    "cleaned": False,
    "result": None,
    "error": {
        "code": "ADMIN_EXPORT_JOB_CLEANUP_FAILED",
        "message": "导出文件清理失败",
    },
}


class CleanupArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError("invalid cleanup arguments")

    def exit(self, status: int = 0, message: str | None = None) -> None:
        raise ValueError("invalid cleanup arguments")


def build_export_job_service() -> AdminExportJobService:
    settings = get_settings()
    auth_service = AdminAuthService(
        get_auth_repository(),
        InMemoryFailedLoginRateLimiter.from_settings(settings.security),
    )
    return AdminExportJobService(get_admin_export_job_repository(), auth_service)


def build_storage() -> AdminExportFileStorage:
    return get_admin_export_file_storage()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = CleanupArgumentParser(add_help=False, description="Clean old local admin export files.")
    parser.add_argument("--older-than-days", type=int, default=7)
    parser.add_argument("--limit", type=int, default=100)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(sys.argv[1:] if argv is None else argv)
        if args.older_than_days < 1:
            raise ValueError("older-than-days must be positive")
        cutoff = datetime.now(UTC) - timedelta(days=args.older_than_days)
        result = build_export_job_service().cleanup_succeeded_export_job_files(
            finished_before=cutoff,
            limit=args.limit,
            storage=build_storage(),
        )
    except Exception:
        sys.stdout.write(json.dumps(CLEANUP_ERROR_PAYLOAD, ensure_ascii=False, sort_keys=True))
        sys.stdout.write("\n")
        return 1

    payload = {
        "cleaned": True,
        "result": asdict(result),
        "error": None,
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
