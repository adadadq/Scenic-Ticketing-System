#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -x ".venv/bin/pytest" ]]; then
  PYTEST_BIN=".venv/bin/pytest"
else
  PYTEST_BIN="${PYTEST_BIN:-pytest}"
fi

echo "[backend] visitor purchase flow acceptance"
"$PYTEST_BIN" backend/tests/test_visitor_flow_api.py

echo "[backend] full test suite"
"$PYTEST_BIN" backend/tests
