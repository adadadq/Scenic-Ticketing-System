from __future__ import annotations

import importlib.util
import stat
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT_DIR / "scripts" / "harden-local-database.py"
SPEC = importlib.util.spec_from_file_location("harden_local_database", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_harden_hba_replaces_local_trust_without_touching_unrelated_rules():
    source = """# local development
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
local   replication     all                                     trust
host    replication     all             127.0.0.1/32            trust
host    replication     all             ::1/128                 trust
host    other           other           10.0.0.0/8               reject
"""

    hardened = MODULE.harden_hba(source)

    assert "trust" not in hardened
    assert hardened.count("scram-sha-256") == 4
    assert hardened.count("peer") == 2
    assert "10.0.0.0/8               reject" in hardened


def test_atomic_write_replaces_file_and_sets_private_permissions(tmp_path):
    target = tmp_path / "local-db.env"

    MODULE.atomic_write(target, MODULE.env_text("app-secret", "read-secret"), stat.S_IRUSR | stat.S_IWUSR)

    assert target.stat().st_mode & 0o777 == 0o600
    assert "DB_PASSWORD=app-secret" in target.read_text(encoding="utf-8")
    assert "READONLY_DB_PASSWORD=read-secret" in target.read_text(encoding="utf-8")
