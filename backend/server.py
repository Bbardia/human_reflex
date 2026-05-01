"""aiohttp server hosting the static frontend and the /ws WebSocket endpoint.
The WebSocket pushes session snapshots; nothing is consumed from clients in v1.
"""
import asyncio
import json
import logging
from pathlib import Path
from aiohttp import web, WSMsgType
from backend.config import CONFIG, public_config_dict


log = logging.getLogger(__name__)


class GameServer:
    def __init__(self, snapshot_provider):
        """snapshot_provider: a callable () -> dict — returns the latest session snapshot."""
        self._snapshot_provider = snapshot_provider
        self._clients: set[web.WebSocketResponse] = set()
        self._app = web.Application()
        self._setup_routes()
        self._broadcast_task: asyncio.Task | None = None

    def _setup_routes(self) -> None:
        self._app.router.add_get("/ws", self._ws_handler)
        # Static is added at start() if the dist directory exists

    async def _ws_handler(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse(heartbeat=10.0)
        await ws.prepare(request)
        # Send config dump as the first message
        await ws.send_json({"type": "config", "data": public_config_dict()})
        self._clients.add(ws)
        log.info("client connected; total=%d", len(self._clients))
        try:
            async for msg in ws:
                if msg.type == WSMsgType.ERROR:
                    log.warning("ws error: %s", ws.exception())
        finally:
            self._clients.discard(ws)
            log.info("client disconnected; total=%d", len(self._clients))
        return ws

    async def _broadcast_loop(self) -> None:
        last_payload: str | None = None
        while True:
            await asyncio.sleep(1.0 / 60.0)  # cap at 60 Hz
            if not self._clients:
                continue
            snapshot = self._snapshot_provider()
            payload = json.dumps({"type": "state", "data": snapshot})
            if payload == last_payload:
                continue
            last_payload = payload
            stale: list[web.WebSocketResponse] = []
            for ws in self._clients:
                if ws.closed:
                    stale.append(ws)
                    continue
                try:
                    await ws.send_str(payload)
                except ConnectionResetError:
                    stale.append(ws)
            for ws in stale:
                self._clients.discard(ws)

    async def start(self) -> web.AppRunner:
        static_dir: Path = CONFIG.server.static_dir
        if static_dir.exists():
            index_path = static_dir / "index.html"

            async def serve_index(_request: web.Request) -> web.FileResponse:
                return web.FileResponse(index_path)

            # Explicit / handler so the kiosk URL lands on index.html instead of
            # the directory listing aiohttp shows when show_index=True.
            self._app.router.add_get("/", serve_index)
            self._app.router.add_static("/", str(static_dir))
        runner = web.AppRunner(self._app)
        await runner.setup()
        site = web.TCPSite(runner, CONFIG.server.host, CONFIG.server.port)
        await site.start()
        self._broadcast_task = asyncio.create_task(self._broadcast_loop())
        log.info(
            "serving on http://%s:%d (static=%s)",
            CONFIG.server.host,
            CONFIG.server.port,
            static_dir if static_dir.exists() else "<missing>",
        )
        return runner
