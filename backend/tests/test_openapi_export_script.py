import importlib.util
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPORT_SCRIPT = PROJECT_ROOT / "scripts" / "export-openapi.py"
PROCESS_ADMIN_EXPORT_JOB_SCRIPT = PROJECT_ROOT / "scripts" / "process-admin-export-job.py"
CLEANUP_ADMIN_EXPORT_FILES_SCRIPT = PROJECT_ROOT / "scripts" / "cleanup-admin-export-files.py"
RUN_ADMIN_EXPORT_WORKER_SCRIPT = PROJECT_ROOT / "scripts" / "run-admin-export-worker.py"
ADMIN_EXPORT_WORKER_SYSTEMD_SERVICE = PROJECT_ROOT / "deploy" / "systemd" / (
    "scenic-ticket-admin-export-worker.service"
)
ADMIN_EXPORT_CLEANUP_SYSTEMD_SERVICE = PROJECT_ROOT / "deploy" / "systemd" / (
    "scenic-ticket-admin-export-cleanup.service"
)
ADMIN_EXPORT_CLEANUP_SYSTEMD_TIMER = PROJECT_ROOT / "deploy" / "systemd" / (
    "scenic-ticket-admin-export-cleanup.timer"
)


def load_process_admin_export_job_script():
    spec = importlib.util.spec_from_file_location(
        "process_admin_export_job_script",
        PROCESS_ADMIN_EXPORT_JOB_SCRIPT,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_cleanup_admin_export_files_script():
    spec = importlib.util.spec_from_file_location(
        "cleanup_admin_export_files_script",
        CLEANUP_ADMIN_EXPORT_FILES_SCRIPT,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_run_admin_export_worker_script():
    spec = importlib.util.spec_from_file_location(
        "run_admin_export_worker_script",
        RUN_ADMIN_EXPORT_WORKER_SCRIPT,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_export_openapi_script_writes_frontend_contract_to_stdout():
    result = subprocess.run(
        [str(EXPORT_SCRIPT)],
        check=True,
        capture_output=True,
        cwd=PROJECT_ROOT,
        text=True,
    )

    openapi = json.loads(result.stdout)

    assert openapi["openapi"].startswith("3.")
    assert "ApiFailureDTO" in openapi["components"]["schemas"]
    assert "HTTPValidationError" not in openapi["components"]["schemas"]
    assert (
        openapi["paths"]["/api/orders"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]
        == {"$ref": "#/components/schemas/ApiSuccessDTO_OrderMeDTO_"}
    )


def test_export_openapi_script_can_write_to_file(tmp_path):
    output_path = tmp_path / "openapi.json"

    subprocess.run(
        [str(EXPORT_SCRIPT), str(output_path)],
        check=True,
        cwd=PROJECT_ROOT,
        text=True,
    )

    openapi = json.loads(output_path.read_text(encoding="utf-8"))

    assert openapi["paths"]["/api/auth/csrf"]["get"]["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ApiSuccessDTO_CsrfPayloadDTO_"
    }


def test_process_admin_export_job_script_documents_single_job_worker_contract():
    script = PROCESS_ADMIN_EXPORT_JOB_SCRIPT.read_text(encoding="utf-8")

    assert os.access(PROCESS_ADMIN_EXPORT_JOB_SCRIPT, os.X_OK)
    assert "AdminExportJobWorkerService" in script
    assert "process_next_pending_job()" in script
    assert '"processed": processed_job is not None' in script
    assert "public_export_job_payload(processed_job)" in script


def test_cleanup_admin_export_files_script_documents_local_file_cleanup_contract():
    script = CLEANUP_ADMIN_EXPORT_FILES_SCRIPT.read_text(encoding="utf-8")

    assert os.access(CLEANUP_ADMIN_EXPORT_FILES_SCRIPT, os.X_OK)
    assert "cleanup_succeeded_export_job_files" in script
    assert "--older-than-days" in script
    assert "--limit" in script
    assert '"cleaned": True' in script
    assert "asdict(result)" in script


def test_run_admin_export_worker_script_documents_loop_contract():
    script = RUN_ADMIN_EXPORT_WORKER_SCRIPT.read_text(encoding="utf-8")

    assert os.access(RUN_ADMIN_EXPORT_WORKER_SCRIPT, os.X_OK)
    assert "run_worker_loop" in script
    assert "process_next_pending_job()" in script
    assert "from app." not in script.split("def load_runtime_dependencies", maxsplit=1)[0]
    assert "--max-jobs" in script
    assert "--max-idle-loops" in script
    assert "--idle-sleep-seconds" in script
    assert '"processed": processed' in script
    assert "public_export_job_payload(job)" in script


def test_admin_export_worker_systemd_service_documents_supervised_loop_contract():
    service = ADMIN_EXPORT_WORKER_SYSTEMD_SERVICE.read_text(encoding="utf-8")

    assert "User=scenic-ticket" in service
    assert "Group=scenic-ticket" in service
    assert "EnvironmentFile=/etc/scenic-ticket/backend.env" in service
    assert "Environment=ADMIN_EXPORT_STORAGE_DIR=/var/lib/scenic-ticket/admin-exports" in service
    assert "ExecStart=/opt/scenic-ticket/current/.venv/bin/python" in service
    assert "scripts/run-admin-export-worker.py --idle-sleep-seconds 5" in service
    assert "Restart=always" in service
    assert "RestartSec=5" in service
    assert "KillSignal=SIGINT" in service
    assert "TimeoutStopSec=30" in service
    assert "StandardOutput=journal" in service
    assert "StandardError=journal" in service
    assert "SyslogIdentifier=scenic-ticket-admin-export-worker" in service
    assert "NoNewPrivileges=true" in service
    assert "PrivateTmp=true" in service
    assert "ProtectSystem=strict" in service
    assert "ProtectHome=true" in service
    assert "ReadWritePaths=/var/lib/scenic-ticket/admin-exports" in service
    assert "StateDirectory=" not in service
    assert "UMask=0077" in service


def test_admin_export_cleanup_systemd_timer_documents_scheduled_cleanup_contract():
    service = ADMIN_EXPORT_CLEANUP_SYSTEMD_SERVICE.read_text(encoding="utf-8")
    timer = ADMIN_EXPORT_CLEANUP_SYSTEMD_TIMER.read_text(encoding="utf-8")

    assert "Type=oneshot" in service
    assert "User=scenic-ticket" in service
    assert "Group=scenic-ticket" in service
    assert "EnvironmentFile=/etc/scenic-ticket/backend.env" in service
    assert "Environment=ADMIN_EXPORT_STORAGE_DIR=/var/lib/scenic-ticket/admin-exports" in service
    assert "ExecStart=/opt/scenic-ticket/current/.venv/bin/python" in service
    assert "scripts/cleanup-admin-export-files.py --older-than-days 7 --limit 100" in service
    assert "Restart=always" not in service
    assert "StandardOutput=journal" in service
    assert "StandardError=journal" in service
    assert "SyslogIdentifier=scenic-ticket-admin-export-cleanup" in service
    assert "NoNewPrivileges=true" in service
    assert "PrivateTmp=true" in service
    assert "ProtectSystem=strict" in service
    assert "ProtectHome=true" in service
    assert "ReadWritePaths=/var/lib/scenic-ticket/admin-exports" in service
    assert "StateDirectory=" not in service
    assert "UMask=0077" in service

    assert "OnCalendar=daily" in timer
    assert "RandomizedDelaySec=30m" in timer
    assert "Persistent=true" in timer
    assert "Unit=scenic-ticket-admin-export-cleanup.service" in timer
    assert "WantedBy=timers.target" in timer


def test_process_admin_export_job_script_builds_worker_with_check_in_and_refund_services(monkeypatch):
    module = load_process_admin_export_job_script()
    worker = object()
    calls = {}

    monkeypatch.setattr(
        module,
        "get_settings",
        lambda: SimpleNamespace(security="security-settings", admin_export_storage_dir="/tmp/export-jobs"),
    )

    class FakeLimiter:
        @staticmethod
        def from_settings(security):
            calls["limiter_security"] = security
            return "limiter"

    def fake_auth_service(auth_repository, limiter):
        calls["auth_service"] = (auth_repository, limiter)
        return "auth-service"

    def fake_export_job_service(export_repository, auth_service):
        calls["export_job_service"] = (export_repository, auth_service)
        return "export-job-service"

    def fake_report_service(order_repository, auth_service):
        calls["report_service"] = (order_repository, auth_service)
        return "report-service"

    def fake_check_in_service(order_repository, auth_service):
        calls["check_in_service"] = (order_repository, auth_service)
        return "check-in-service"

    def fake_refund_service(order_repository, auth_service):
        calls["refund_service"] = (order_repository, auth_service)
        return "refund-service"

    def fake_worker_service(export_job_service, report_service, check_in_service, refund_service, storage):
        calls["worker_service"] = (export_job_service, report_service, check_in_service, refund_service, storage)
        return worker

    monkeypatch.setattr(module, "InMemoryFailedLoginRateLimiter", FakeLimiter)
    monkeypatch.setattr(module, "get_auth_repository", lambda: "auth-repository")
    monkeypatch.setattr(module, "get_admin_export_job_repository", lambda: "export-repository")
    monkeypatch.setattr(module, "get_order_repository", lambda: "order-repository")
    monkeypatch.setattr(module, "AdminAuthService", fake_auth_service)
    monkeypatch.setattr(module, "AdminExportJobService", fake_export_job_service)
    monkeypatch.setattr(module, "AdminReportService", fake_report_service)
    monkeypatch.setattr(module, "AdminCheckInService", fake_check_in_service)
    monkeypatch.setattr(module, "AdminRefundService", fake_refund_service)
    monkeypatch.setattr(module, "get_admin_export_file_storage", lambda: "storage")
    monkeypatch.setattr(module, "AdminExportJobWorkerService", fake_worker_service)

    built_worker = module.build_worker_service()

    assert built_worker is worker
    assert calls["limiter_security"] == "security-settings"
    assert calls["auth_service"] == ("auth-repository", "limiter")
    assert calls["export_job_service"] == ("export-repository", "auth-service")
    assert calls["report_service"] == ("order-repository", "auth-service")
    assert calls["check_in_service"] == ("order-repository", "auth-service")
    assert calls["refund_service"] == ("order-repository", "auth-service")
    assert calls["worker_service"] == (
        "export-job-service",
        "report-service",
        "check-in-service",
        "refund-service",
        "storage",
    )


def test_cleanup_admin_export_files_script_builds_service_and_storage(monkeypatch):
    module = load_cleanup_admin_export_files_script()
    calls = {}

    monkeypatch.setattr(
        module,
        "get_settings",
        lambda: SimpleNamespace(security="security-settings", admin_export_storage_dir="/tmp/export-jobs"),
    )

    class FakeLimiter:
        @staticmethod
        def from_settings(security):
            calls["limiter_security"] = security
            return "limiter"

    def fake_auth_service(auth_repository, limiter):
        calls["auth_service"] = (auth_repository, limiter)
        return "auth-service"

    def fake_export_job_service(export_repository, auth_service):
        calls["export_job_service"] = (export_repository, auth_service)
        return "export-job-service"

    monkeypatch.setattr(module, "InMemoryFailedLoginRateLimiter", FakeLimiter)
    monkeypatch.setattr(module, "get_auth_repository", lambda: "auth-repository")
    monkeypatch.setattr(module, "get_admin_export_job_repository", lambda: "export-repository")
    monkeypatch.setattr(module, "AdminAuthService", fake_auth_service)
    monkeypatch.setattr(module, "AdminExportJobService", fake_export_job_service)
    monkeypatch.setattr(module, "get_admin_export_file_storage", lambda: "storage")

    built_service = module.build_export_job_service()
    built_storage = module.build_storage()

    assert built_service == "export-job-service"
    assert built_storage == "storage"
    assert calls["limiter_security"] == "security-settings"
    assert calls["auth_service"] == ("auth-repository", "limiter")
    assert calls["export_job_service"] == ("export-repository", "auth-service")


def test_run_admin_export_worker_script_builds_worker_with_report_services(monkeypatch):
    module = load_run_admin_export_worker_script()
    worker = object()
    calls = {}

    class FakeLimiter:
        @staticmethod
        def from_settings(security):
            calls["limiter_security"] = security
            return "limiter"

    def fake_auth_service(auth_repository, limiter):
        calls["auth_service"] = (auth_repository, limiter)
        return "auth-service"

    def fake_export_job_service(export_repository, auth_service):
        calls["export_job_service"] = (export_repository, auth_service)
        return "export-job-service"

    def fake_report_service(order_repository, auth_service):
        calls["report_service"] = (order_repository, auth_service)
        return "report-service"

    def fake_check_in_service(order_repository, auth_service):
        calls["check_in_service"] = (order_repository, auth_service)
        return "check-in-service"

    def fake_refund_service(order_repository, auth_service):
        calls["refund_service"] = (order_repository, auth_service)
        return "refund-service"

    def fake_worker_service(export_job_service, report_service, check_in_service, refund_service, storage):
        calls["worker_service"] = (export_job_service, report_service, check_in_service, refund_service, storage)
        return worker

    monkeypatch.setattr(
        module,
        "load_runtime_dependencies",
        lambda: SimpleNamespace(
            get_settings=lambda: SimpleNamespace(
                security="security-settings",
                admin_export_storage_dir="/tmp/export-jobs",
            ),
            get_auth_repository=lambda: "auth-repository",
            get_admin_export_job_repository=lambda: "export-repository",
            get_order_repository=lambda: "order-repository",
            AdminAuthService=fake_auth_service,
            AdminExportJobService=fake_export_job_service,
            AdminReportService=fake_report_service,
            AdminCheckInService=fake_check_in_service,
            AdminRefundService=fake_refund_service,
            get_admin_export_file_storage=lambda: "storage",
            AdminExportJobWorkerService=fake_worker_service,
            InMemoryFailedLoginRateLimiter=FakeLimiter,
        ),
    )

    built_worker = module.build_worker_service()

    assert built_worker is worker
    assert calls["limiter_security"] == "security-settings"
    assert calls["auth_service"] == ("auth-repository", "limiter")
    assert calls["export_job_service"] == ("export-repository", "auth-service")
    assert calls["report_service"] == ("order-repository", "auth-service")
    assert calls["check_in_service"] == ("order-repository", "auth-service")
    assert calls["refund_service"] == ("order-repository", "auth-service")
    assert calls["worker_service"] == (
        "export-job-service",
        "report-service",
        "check-in-service",
        "refund-service",
        "storage",
    )


def test_cleanup_admin_export_files_script_outputs_sanitized_json(monkeypatch, capsys):
    module = load_cleanup_admin_export_files_script()

    @dataclass(frozen=True)
    class FakeCleanupResult:
        scanned: int
        files_deleted: int
        files_missing: int
        metadata_cleared: int
        skipped: int

    result = FakeCleanupResult(
        scanned=2,
        files_deleted=1,
        files_missing=1,
        metadata_cleared=2,
        skipped=0,
    )
    calls = {}

    class FakeService:
        def cleanup_succeeded_export_job_files(self, *, finished_before, limit, storage):
            calls["cleanup"] = (finished_before, limit, storage)
            return result

    monkeypatch.setattr(module, "build_export_job_service", lambda: FakeService())
    monkeypatch.setattr(module, "build_storage", lambda: "storage")

    exit_code = module.main(["--older-than-days", "3", "--limit", "50"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload == {
        "cleaned": True,
        "result": {
            "files_deleted": 1,
            "files_missing": 1,
            "metadata_cleared": 2,
            "scanned": 2,
            "skipped": 0,
        },
        "error": None,
    }
    assert calls["cleanup"][1:] == (50, "storage")
    assert captured.err == ""


def test_cleanup_admin_export_files_script_sanitizes_errors(monkeypatch, capsys):
    module = load_cleanup_admin_export_files_script()

    def raise_cleanup_error():
        raise RuntimeError("secret SQL and /tmp/private/path")

    monkeypatch.setattr(module, "build_export_job_service", raise_cleanup_error)

    exit_code = module.main([])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 1
    assert payload == {
        "cleaned": False,
        "result": None,
        "error": {
            "code": "ADMIN_EXPORT_JOB_CLEANUP_FAILED",
            "message": "导出文件清理失败",
        },
    }
    assert captured.err == ""
    assert "secret" not in captured.out
    assert "/tmp/private/path" not in captured.out


def test_cleanup_admin_export_files_script_rejects_non_positive_retention_days(capsys):
    module = load_cleanup_admin_export_files_script()

    exit_code = module.main(["--older-than-days", "0"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 1
    assert payload["cleaned"] is False
    assert payload["error"]["code"] == "ADMIN_EXPORT_JOB_CLEANUP_FAILED"
    assert captured.err == ""


def test_cleanup_admin_export_files_script_sanitizes_argument_errors(capsys):
    module = load_cleanup_admin_export_files_script()

    for argv in (["--limit", "not-a-number"], ["--help"]):
        exit_code = module.main(argv)
        captured = capsys.readouterr()
        payload = json.loads(captured.out)

        assert exit_code == 1
        assert payload == {
            "cleaned": False,
            "result": None,
            "error": {
                "code": "ADMIN_EXPORT_JOB_CLEANUP_FAILED",
                "message": "导出文件清理失败",
            },
        }
        assert captured.err == ""


def test_run_admin_export_worker_script_processes_until_limits(monkeypatch, capsys):
    module = load_run_admin_export_worker_script()

    class FakeJob:
        def __init__(self, job_id: str):
            self.job_id = job_id

        def model_dump(self, *, by_alias, exclude_none, mode):
            assert by_alias is True
            assert exclude_none is True
            assert mode == "json"
            return {"jobId": self.job_id, "status": "SUCCEEDED"}

    class FakeWorker:
        def __init__(self):
            self.jobs = [FakeJob("job-1"), FakeJob("job-2"), None]

        def process_next_pending_job(self):
            return self.jobs.pop(0)

    sleeps: list[float] = []
    monkeypatch.setattr(module.time, "sleep", lambda seconds: sleeps.append(seconds))

    result = module.run_worker_loop(
        FakeWorker(),
        max_jobs=2,
        max_idle_loops=0,
        idle_sleep_seconds=0.25,
    )

    assert result == {
        "running": False,
        "processed": 2,
        "idleLoops": 0,
        "lastJob": {"jobId": "job-2", "status": "SUCCEEDED"},
        "error": None,
    }
    assert sleeps == []

    monkeypatch.setattr(module, "build_worker_service", lambda: FakeWorker())
    exit_code = module.main(["--max-jobs", "1", "--idle-sleep-seconds", "0"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["processed"] == 1
    assert payload["idleLoops"] == 0
    assert payload["lastJob"] == {"jobId": "job-1", "status": "SUCCEEDED"}
    assert payload["error"] is None
    assert captured.err == ""


def test_process_admin_export_job_script_redacts_public_job_filters(monkeypatch, capsys):
    module = load_process_admin_export_job_script()

    class FakeJob:
        def model_dump(self, *, by_alias, exclude_none, mode):
            assert by_alias is True
            assert exclude_none is True
            assert mode == "json"
            return {
                "jobId": "job-1",
                "status": "SUCCEEDED",
                "filters": {
                    "ticketCode": "TICKET-SECRET",
                    "orderNo": "ORDER-SECRET",
                    "operatorUsername": "admin-secret",
                    "dateFrom": "2026-07-01",
                },
            }

    class FakeWorker:
        def process_next_pending_job(self):
            return FakeJob()

    monkeypatch.setattr(module, "build_worker_service", lambda: FakeWorker())

    exit_code = module.main()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["processed"] is True
    assert payload["job"]["filters"] == {
        "ticketCode": "***",
        "orderNo": "***",
        "operatorUsername": "***",
        "dateFrom": "2026-07-01",
    }
    assert captured.err == ""


def test_run_admin_export_worker_script_redacts_public_last_job_filters(monkeypatch):
    module = load_run_admin_export_worker_script()

    class FakeJob:
        def model_dump(self, *, by_alias, exclude_none, mode):
            assert by_alias is True
            assert exclude_none is True
            assert mode == "json"
            return {
                "jobId": "job-1",
                "status": "SUCCEEDED",
                "filters": {
                    "ticketCode": "TICKET-SECRET",
                    "orderNo": "ORDER-SECRET",
                    "operatorUsername": "admin-secret",
                    "includeEmpty": True,
                },
            }

    class FakeWorker:
        def process_next_pending_job(self):
            return FakeJob()

    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)

    result = module.run_worker_loop(
        FakeWorker(),
        max_jobs=1,
        max_idle_loops=0,
        idle_sleep_seconds=0,
    )

    assert result["processed"] == 1
    assert result["lastJob"]["filters"] == {
        "ticketCode": "***",
        "orderNo": "***",
        "operatorUsername": "***",
        "includeEmpty": True,
    }


def test_run_admin_export_worker_script_stops_after_idle_limit(monkeypatch):
    module = load_run_admin_export_worker_script()

    class IdleWorker:
        def process_next_pending_job(self):
            return None

    sleeps: list[float] = []
    monkeypatch.setattr(module.time, "sleep", lambda seconds: sleeps.append(seconds))

    result = module.run_worker_loop(
        IdleWorker(),
        max_jobs=0,
        max_idle_loops=3,
        idle_sleep_seconds=0.5,
    )

    assert result == {
        "running": False,
        "processed": 0,
        "idleLoops": 3,
        "lastJob": None,
        "error": None,
    }
    assert sleeps == [0.5, 0.5]


def test_run_admin_export_worker_script_sanitizes_errors(monkeypatch, capsys):
    module = load_run_admin_export_worker_script()

    def raise_boot_error():
        raise RuntimeError("secret SQL and /tmp/private/path")

    monkeypatch.setattr(module, "build_worker_service", raise_boot_error)

    exit_code = module.main([])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 1
    assert payload == {
        "running": False,
        "processed": 0,
        "idleLoops": 0,
        "lastJob": None,
        "error": {
            "code": "ADMIN_EXPORT_WORKER_LOOP_FAILED",
            "message": "导出任务 worker 循环失败",
        },
    }
    assert captured.err == ""
    assert "secret" not in captured.out
    assert "/tmp/private/path" not in captured.out


def test_run_admin_export_worker_script_sanitizes_import_errors(monkeypatch, capsys):
    module = load_run_admin_export_worker_script()

    def raise_import_error():
        raise ImportError("secret import path /tmp/private/module.py")

    monkeypatch.setattr(module, "ensure_backend_path", raise_import_error)

    exit_code = module.main(["--max-idle-loops", "1", "--idle-sleep-seconds", "0"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 1
    assert payload["error"]["code"] == "ADMIN_EXPORT_WORKER_LOOP_FAILED"
    assert captured.err == ""
    assert "secret import path" not in captured.out
    assert "/tmp/private/module.py" not in captured.out


def test_run_admin_export_worker_script_reexec_uses_supplied_argv(monkeypatch, tmp_path):
    module = load_run_admin_export_worker_script()
    fake_python = tmp_path / "python"
    fake_python.write_text("", encoding="utf-8")
    calls = {}

    class ExecCalled(Exception):
        pass

    def fake_execv(executable, args):
        calls["execv"] = (executable, args)
        raise ExecCalled

    monkeypatch.setattr(module, "VENV_PYTHON", fake_python)
    monkeypatch.setattr(module, "VENV_DIR", tmp_path)
    monkeypatch.setattr(module.sys, "prefix", str(tmp_path / "outside"))
    monkeypatch.setattr(module.os, "execv", fake_execv)

    with pytest.raises(ExecCalled):
        module.maybe_reexec_with_venv(["--max-jobs", "7"])

    assert calls["execv"] == (
        str(fake_python),
        [str(fake_python), str(module.Path(module.__file__).resolve()), "--max-jobs", "7"],
    )


def test_run_admin_export_worker_script_sanitizes_argument_errors(capsys):
    module = load_run_admin_export_worker_script()

    invalid_args = [
        ["--max-jobs", "-1"],
        ["--max-idle-loops", "-1"],
        ["--idle-sleep-seconds", "-0.1"],
        ["--idle-sleep-seconds", "3600.1"],
        ["--idle-sleep-seconds", "not-a-number"],
        ["--idle-sleep-seconds", "nan"],
        ["--idle-sleep-seconds", "inf"],
        ["--help"],
    ]

    for argv in invalid_args:
        exit_code = module.main(argv)
        captured = capsys.readouterr()
        payload = json.loads(captured.out)

        assert exit_code == 1
        assert payload["error"]["code"] == "ADMIN_EXPORT_WORKER_LOOP_FAILED"
        assert captured.err == ""


def test_process_admin_export_job_script_sanitizes_worker_boot_errors(monkeypatch, capsys):
    module = load_process_admin_export_job_script()

    def raise_boot_error():
        raise RuntimeError("secret SQL and /tmp/private/path")

    monkeypatch.setattr(module, "build_worker_service", raise_boot_error)

    exit_code = module.main()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 1
    assert payload == {
        "processed": False,
        "job": None,
        "error": {
            "code": "ADMIN_EXPORT_JOB_WORKER_FAILED",
            "message": "导出任务处理失败",
        },
    }
    assert captured.err == ""
    assert "secret" not in captured.out
    assert "/tmp/private/path" not in captured.out
