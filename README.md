# Human Reflex

Two-player, pose-driven reflex competition. Designed for an Intel NUC kiosk running Ubuntu, with a single wide-angle USB webcam.

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python scripts/download_model.py

cd frontend
npm install
npm run build
cd ..
```

## Run (development)

In two terminals:

```bash
# Terminal 1: backend
source .venv/bin/activate
python -m backend.app

# Terminal 2: frontend dev server (HMR)
cd frontend && npm run dev
```

Open `http://localhost:5173` in a browser. Backend WebSocket runs on `ws://localhost:8765/ws`.

## Run (kiosk-style, single port)

```bash
cd frontend && npm run build && cd ..
python -m backend.app
chromium --kiosk --app=http://localhost:8765
```

## Kiosk autostart (NUC)

To make the app boot automatically into the Chromium kiosk on the NUC:

1. Install the project at `~/Sensopro/Side_quest/Human Reflex` (or edit the path in `kiosk/human-reflex.service`).
2. Make sure `chromium` (or `chromium-browser`) is installed system-wide.
3. Copy the user-level systemd unit:
   ```bash
   mkdir -p ~/.config/systemd/user
   cp kiosk/human-reflex.service ~/.config/systemd/user/
   ```
4. Enable + start:
   ```bash
   systemctl --user daemon-reload
   systemctl --user enable --now human-reflex.service
   ```
5. To watch logs:
   ```bash
   journalctl --user -u human-reflex.service -f
   ```
6. To disable autostart:
   ```bash
   systemctl --user disable --now human-reflex.service
   ```

`kiosk/start.sh` builds the frontend if `frontend/dist/` is missing or stale, then launches the backend and Chromium. Both processes share the systemd service's lifetime — when one exits, the other is killed and the unit restarts.
