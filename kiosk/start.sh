#!/usr/bin/env bash
# kiosk/start.sh — boots the Human Reflex backend + Chromium kiosk on the NUC.
# Idempotent enough to be invoked by systemd at login. Logs to journalctl.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Activate venv (assumes it exists — see README setup)
# shellcheck disable=SC1091
source .venv/bin/activate

# Build the frontend if dist is missing or stale
if [ ! -d frontend/dist ] || [ frontend/src -nt frontend/dist ]; then
  echo "[start.sh] building frontend..."
  ( cd frontend && npm run build )
fi

# Launch the backend (systemd manages the process)
python -m backend.app &
BACKEND_PID=$!

# Wait briefly for the server to come up
for i in $(seq 1 30); do
  if curl -sf http://127.0.0.1:8765/ >/dev/null 2>&1; then
    break
  fi
  sleep 0.2
done

# Launch chromium in kiosk mode (fail loudly if not installed)
if command -v chromium >/dev/null 2>&1; then
  CHROMIUM_BIN=chromium
elif command -v chromium-browser >/dev/null 2>&1; then
  CHROMIUM_BIN=chromium-browser
else
  echo "[start.sh] chromium not found; backend running but no kiosk window" >&2
  wait "$BACKEND_PID"
  exit 1
fi

"$CHROMIUM_BIN" \
  --kiosk \
  --app=http://127.0.0.1:8765 \
  --noerrdialogs \
  --disable-translate \
  --disable-features=TranslateUI \
  --autoplay-policy=no-user-gesture-required \
  --disable-pinch \
  --overscroll-history-navigation=0 &
CHROMIUM_PID=$!

# Tie our lifetime to whichever child exits first
wait -n "$BACKEND_PID" "$CHROMIUM_PID"
EXIT_CODE=$?
kill "$BACKEND_PID" "$CHROMIUM_PID" 2>/dev/null || true
exit "$EXIT_CODE"
