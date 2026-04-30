"""Wraps the OpenVINO YOLOv8-Pose model. Inputs frames, outputs Pose objects."""
from pathlib import Path
import numpy as np
from ultralytics import YOLO
from backend.pose.types import Pose


class PoseEngine:
    def __init__(self, model_dir: Path, conf: float = 0.4, iou: float = 0.5, max_persons: int = 2):
        if not model_dir.exists():
            raise FileNotFoundError(
                f"Pose model not found at {model_dir}. Run scripts/download_model.py."
            )
        self._model = YOLO(str(model_dir))
        self._conf = conf
        self._iou = iou
        self._max_persons = max_persons

    def infer(self, frame_bgr: np.ndarray) -> list[Pose]:
        """frame_bgr: HxWx3 uint8 BGR image (from OpenCV)."""
        h, w = frame_bgr.shape[:2]
        results = self._model.predict(
            source=frame_bgr,
            conf=self._conf,
            iou=self._iou,
            max_det=self._max_persons,
            verbose=False,
        )
        if not results:
            return []
        r = results[0]
        if r.keypoints is None or r.boxes is None:
            return []

        kps = r.keypoints.data.cpu().numpy()  # (N, 17, 3): x, y, conf
        boxes = r.boxes.xyxy.cpu().numpy()    # (N, 4)
        scores = r.boxes.conf.cpu().numpy()   # (N,)

        poses: list[Pose] = []
        for i in range(len(boxes)):
            kp = kps[i].copy()
            kp[:, 0] /= w
            kp[:, 1] /= h
            x0, y0, x1, y1 = boxes[i] / np.array([w, h, w, h])
            poses.append(Pose(
                keypoints=kp.astype(np.float32),
                bbox=(float(x0), float(y0), float(x1), float(y1)),
                score=float(scores[i]),
            ))
        return poses
