#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ -x /tmp/monapp-venv2/bin/python ]]; then
  PY=/tmp/monapp-venv2/bin/python
elif [[ -x .venv/bin/python ]]; then
  PY=.venv/bin/python
else
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
  PY=.venv/bin/python
fi

unset ADMIN_USERNAME ADMIN_PASSWORD || true
export PORT="${PORT:-5303}"
exec "$PY" app.py
