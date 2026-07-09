#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

OPENAPI_TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$OPENAPI_TMP_DIR"' EXIT

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
else
  PYTHON_BIN="${PYTHON_BIN:-python3}"
fi

echo "[integration] backend acceptance and test suite"
scripts/verify-backend.sh

echo "[integration] export backend OpenAPI contract"
scripts/export-openapi.py "$OPENAPI_TMP_DIR/openapi.json"
test -s "$OPENAPI_TMP_DIR/openapi.json"
"$PYTHON_BIN" - "$OPENAPI_TMP_DIR/openapi.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as openapi_file:
    openapi = json.load(openapi_file)

if not openapi.get("paths"):
    raise SystemExit("exported OpenAPI contract must include paths")
if not openapi.get("components", {}).get("schemas"):
    raise SystemExit("exported OpenAPI contract must include component schemas")
PY

echo "[integration] frontend build against shared API contract"
if [[ ! -d "frontend/node_modules" ]]; then
  echo "[integration] frontend/node_modules missing; running npm ci"
  (cd frontend && npm ci)
fi
(cd frontend && npm run lint)
(cd frontend && npm run build)

case "${VERIFY_INTEGRATION_E2E:-0}" in
  0|"")
    ;;
  1|mock)
    echo "[integration] optional frontend e2e smoke against mock API"
    (cd frontend && E2E_API_BASE_URL= npm run test:e2e)
    ;;
  real)
    REAL_E2E_API_BASE_URL="${E2E_API_BASE_URL:-http://127.0.0.1:8000}"
    echo "[integration] optional frontend e2e smoke against real API at ${REAL_E2E_API_BASE_URL}"
    (cd frontend && E2E_API_BASE_URL="$REAL_E2E_API_BASE_URL" npm run test:e2e)
    ;;
  *)
    echo "[integration] VERIFY_INTEGRATION_E2E must be 0, 1, mock, or real" >&2
    exit 2
    ;;
esac
