"""aiohttp server hosting the static frontend, the /ws WebSocket, and the
/stream.mjpg camera feed. The WebSocket pushes session snapshots; the MJPEG
endpoint streams JPEG frames at ~30 fps so the browser can render the live
camera as the background under the pose skeletons.
"""
import asyncio
import json
import logging
from pathlib import Path

import cv2
from aiohttp import web, WSMsgType
from backend.config import CONFIG, public_config_dict


log = logging.getLogger(__name__)

STREAM_FPS = 30
STREAM_JPEG_QUALITY = 65


class GameServer:
    def __init__(self, snapshot_provider, frame_provider=None):
        """snapshot_provider: () -> dict — returns the latest session snapshot.
        frame_provider: () -> Frame | None — returns the latest camera frame
            (with .image and .timestamp_ms). Optional — if missing, /stream.mjpg
            returns 503.
        """
        self._snapshot_provider = snapshot_provider
        self._frame_provider = frame_provider
        self._clients: set[web.WebSocketResponse] = set()
        self._app = web.Application()
        self._setup_routes()
        self._broadcast_task: asyncio.Task | None = None

    def _setup_routes(self) -> None:
        self._app.router.add_get("/ws", self._ws_handler)
        self._app.router.add_get("/stream.mjpg", self._stream_handler)
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

    async def _stream_handler(self, request: web.Request) -> web.StreamResponse:
        if self._frame_provider is None:
            return web.Response(status=503, text="camera not wired")
        boundary = "frame"
        resp = web.StreamResponse(
            status=200,
            reason="OK",
            headers={
                "Content-Type": f"multipart/x-mixed-replace; boundary={boundary}",
                "Cache-Control": "no-cache, private",
                "Pragma": "no-cache",
            },
        )
        await resp.prepare(request)
        loop = asyncio.get_running_loop()
        last_ts: int | None = None
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), STREAM_JPEG_QUALITY]
        try:
            while True:
                frame = self._frame_provider()
                if frame is None or frame.timestamp_ms == last_ts:
                    await asyncio.sleep(1.0 / STREAM_FPS)
                    continue
                last_ts = frame.timestamp_ms
                ok, buf = await loop.run_in_executor(
                    None, cv2.imencode, ".jpg", frame.image, encode_params
                )
                if not ok:
                    await asyncio.sleep(1.0 / STREAM_FPS)
                    continue
                jpg = buf.tobytes()
                chunk = (
                    f"--{boundary}\r\n"
                    f"Content-Type: image/jpeg\r\n"
                    f"Content-Length: {len(jpg)}\r\n\r\n"
                ).encode() + jpg + b"\r\n"
                await resp.write(chunk)
                await asyncio.sleep(1.0 / STREAM_FPS)
        except (ConnectionResetError, asyncio.CancelledError):
            pass
        return resp

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
