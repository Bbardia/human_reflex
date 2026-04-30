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
