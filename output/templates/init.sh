#!/usr/bin/env bash
# Standard startup + baseline verification for a two-stack repo
# (Python backend + React frontend). Adapted from the course template:
# same contract (install -> verify -> print start command), extended to
# run both stacks and fail fast on the first broken baseline.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# ---- Adjust these to the target repository ---------------------------------
BACKEND_DIR="backend"          # e.g. ./backend or ./server
FRONTEND_DIR="frontend"        # e.g. ./frontend or ./client

BACKEND_INSTALL_CMD=(uv sync)                       # or: pip install -r requirements.txt
BACKEND_VERIFY_CMDS=(
  "uv run pytest || [ \$? -eq 5 ]"                  # exit 5 = no tests collected; not a failure
  "uv run ruff check ."
  # "uv run mypy ."
)
BACKEND_START_CMD="uv run uvicorn app.main:app --reload"

FRONTEND_INSTALL_CMD=(npm install)
FRONTEND_VERIFY_CMDS=(
  "npm run lint"
  "npm test -- --run"
  "npm run build"
)
FRONTEND_START_CMD="npm run dev"

# Optional: deploy-surface validation (Cloud Run / GCP). Keep it a DRY RUN —
# init.sh must never mutate cloud state.
DEPLOY_CHECK_CMD=""            # e.g. "gcloud run services describe <svc> --region <r> --format=none"
# -----------------------------------------------------------------------------

run_step() {
  echo "==> $1"
  shift
  bash -c "$*"
}

echo "==> Working directory: $PWD"

echo "==> [backend] Syncing dependencies"
(cd "$BACKEND_DIR" && "${BACKEND_INSTALL_CMD[@]}")

for cmd in "${BACKEND_VERIFY_CMDS[@]}"; do
  (cd "$BACKEND_DIR" && run_step "[backend] $cmd" "$cmd")
done

echo "==> [frontend] Syncing dependencies"
(cd "$FRONTEND_DIR" && "${FRONTEND_INSTALL_CMD[@]}")

for cmd in "${FRONTEND_VERIFY_CMDS[@]}"; do
  (cd "$FRONTEND_DIR" && run_step "[frontend] $cmd" "$cmd")
done

if [ -n "$DEPLOY_CHECK_CMD" ]; then
  run_step "[deploy] $DEPLOY_CHECK_CMD" "$DEPLOY_CHECK_CMD"
fi

echo "==> Baseline verification complete"
echo ""
echo "Start commands:"
echo "    backend : (cd $BACKEND_DIR && $BACKEND_START_CMD)"
echo "    frontend: (cd $FRONTEND_DIR && $FRONTEND_START_CMD)"
echo ""
echo "Next steps:"
echo "1. Read .planning/STATE.md and feature_list.json for current state"
echo "2. Pick ONE unfinished feature/phase to work on"
echo "3. Delegate implementation to an ephemeral subagent with a self-contained brief"
echo "4. Re-run ./init.sh before claiming done"
