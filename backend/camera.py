"""Threaded OpenCV capture. Latest-frame-wins (no buffer build-up)."""
import threading
import time
from dataclasses import dataclass
from typing import Optional
import cv2
import numpy as np
from backend.config import CameraConfig


@dataclass
class Frame:
    image: np.ndarray  # HxWx3 BGR uint8
    timestamp_ms: int


class Camera:
    def __init__(self, config: CameraConfig):
        self._config = config
        self._cap: Optional[cv2.VideoCapture] = None
        self._latest: Optional[Frame] = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        cap = cv2.VideoCapture(self._config.device_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._config.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._config.height)
        cap.set(cv2.CAP_PROP_FPS, self._config.fps)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open camera index {self._config.device_index}")
        self._cap = cap
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        assert self._cap is not None
        while not self._stop.is_set():
            ok, img = self._cap.read()
            if not ok:
                time.sleep(0.005)
                continue
            ts = int(time.monotonic() * 1000)
            with self._lock:
                self._latest = Frame(image=img, timestamp_ms=ts)

    def get_latest(self) -> Optional[Frame]:
        with self._lock:
            return self._latest

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        if self._cap:
            self._cap.release()
