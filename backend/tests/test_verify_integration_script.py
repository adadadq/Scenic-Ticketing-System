import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VERIFY_INTEGRATION_SCRIPT = PROJECT_ROOT / "scripts" / "verify-integration.sh"


def test_verify_integration_script_keeps_cross_end_gates():
    script = VERIFY_INTEGRATION_SCRIPT.read_text(encoding="utf-8")
    e2e_switch = 'case "${VERIFY_INTEGRATION_E2E:-0}" in'

    assert os.access(VERIFY_INTEGRATION_SCRIPT, os.X_OK)
    assert 'PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"' in script
    assert 'PYTHON_BIN="${PYTHON_BIN:-python3}"' in script
    assert '"$PYTHON_BIN" - "$OPENAPI_TMP_DIR/openapi.json"' in script
    assert "python3 - \"$OPENAPI_TMP_DIR/openapi.json\"" not in script
    assert "scripts/verify-backend.sh" in script
    assert "scripts/export-openapi.py" in script
    assert "json.load(openapi_file)" in script
    assert 'openapi.get("paths")' in script
    assert 'openapi.get("components", {}).get("schemas")' in script
    assert "raise SystemExit" in script
    assert "assert openapi.get" not in script
    assert "npm run lint" in script
    assert "npm run build" in script
    assert e2e_switch in script
    assert "1|mock)" in script
    assert "real)" in script
    assert "npm run test:e2e" in script
    assert "E2E_API_BASE_URL= npm run test:e2e" in script
    assert 'REAL_E2E_API_BASE_URL="${E2E_API_BASE_URL:-http://127.0.0.1:8000}"' in script
    assert 'E2E_API_BASE_URL="$REAL_E2E_API_BASE_URL" npm run test:e2e' in script
    assert "VERIFY_INTEGRATION_E2E must be 0, 1, mock, or real" in script
    assert script.index(e2e_switch) < script.index("npm run test:e2e")
    assert "mktemp -d" in script
    assert "trap 'rm -rf \"$OPENAPI_TMP_DIR\"' EXIT" in script
