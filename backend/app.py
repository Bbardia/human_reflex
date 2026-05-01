"""Wires camera → pose → session → server in one async loop.
Run with: python -m backend.app
"""
import asyncio
import logging
import time
from typing import Optional

from backend.camera import Camera
from backend.config import CONFIG
from backend.player import PlayerRouter
from backend.pose.engine import PoseEngine
from backend.pose.types import Pose
from backend.server import GameServer
from backend.session import Session


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("app")


class App:
    def __init__(self) -> None:
        self.camera = Camera(CONFIG.camera)
        self.pose = PoseEngine(
            CONFIG.pose.model_dir,
            conf=CONFIG.pose.conf_threshold,
            iou=CONFIG.pose.iou_threshold,
            max_persons=CONFIG.pose.max_persons,
        )
        self.router = PlayerRouter()
        self.session = Session(now_ms=int(time.monotonic() * 1000))
        self.server = GameServer(snapshot_provider=self._snapshot)
        self._latest_p1: Optional[Pose] = None
        self._latest_p2: Optional[Pose] = None
        self._latest_now_ms: int = 0

    def _snapshot(self) -> dict:
        return self.session.snapshot(self._latest_now_ms, self._latest_p1, self._latest_p2)

    async def _pipeline_loop(self) -> None:
        """Pulls the latest camera frame, runs pose, advances session.
        Runs the inference in a thread executor so the asyncio loop stays responsive."""
        loop = asyncio.get_running_loop()
        while True:
            frame = self.camera.get_latest()
            if frame is None:
                await asyncio.sleep(0.005)
                continue
            now_ms = int(time.monotonic() * 1000)
            poses = await loop.run_in_executor(None, self.pose.infer, frame.image)
            p1, p2 = self.router.route(poses)
            self.session.tick(now_ms, p1, p2)
            self._latest_p1 = p1
            self._latest_p2 = p2
            self._latest_now_ms = now_ms
            # Yield to the event loop; pace at ~60 Hz max
            await asyncio.sleep(1.0 / 60.0)

    async def run(self) -> None:
        self.camera.start()
        log.info("camera started")
        runner = await self.server.start()
        log.info("server started; entering pipeline")
        try:
            await self._pipeline_loop()
        finally:
            self.camera.stop()
            await runner.cleanup()


def main() -> None:
    asyncio.run(App().run())


if __name__ == "__main__":
    main()
