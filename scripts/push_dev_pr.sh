#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Creating/updating remote main from master..."
git push -u origin master:main

echo "Pushing dev..."
git push -u origin dev

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  gh pr create --base main --head dev \
    --title "Complete increments 3–8: servers, metrics, UX, CI" \
    --body "$(cat <<'BODY'
## Summary
- Servers CRUD UI (list/add/remove) with auth, CSRF, and 10-host cap
- Localhost + SSH metrics collectors wired into dashboard API
- 5s auto-refresh, Chart.js, unreachable-host error states
- Hardening docs (`.env.example`, security notes) and GitHub Actions CI (ruff/pytest/smoke)

## Test plan
- [ ] `pytest -q` passes locally
- [ ] `./start.sh` → login `admin` / `admin123`
- [ ] Dashboard shows localhost metrics and refreshes
- [ ] Add/remove a server on `/servers`
- [ ] CI green on the PR

BODY
)"
else
  echo "Open PR in browser:"
  echo "https://github.com/mith-theone/Monitoring_Application/compare/main...dev?expand=1"
fi
