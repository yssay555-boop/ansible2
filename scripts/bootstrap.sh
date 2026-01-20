#!/usr/bin/env bash
set -euo pipefail

if command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  echo "[ERROR] python3 not found" >&2
  exit 1
fi

$PY -m pip install --upgrade pip >/dev/null
$PY -m pip install "ansible-core>=2.15" ansible-lint molecule molecule-plugins[docker] >/dev/null

ansible-galaxy collection install -r requirements.yml

echo "OK: bootstrap complete"
