"""Pose data types. We use COCO 17-keypoint convention from YOLOv8-Pose."""
from dataclasses import dataclass
import numpy as np


# COCO keypoint indices (matches YOLOv8-Pose output order)
NOSE = 0
LEFT_EYE = 1
RIGHT_EYE = 2
LEFT_EAR = 3
RIGHT_EAR = 4
LEFT_SHOULDER = 5
RIGHT_SHOULDER = 6
LEFT_ELBOW = 7
RIGHT_ELBOW = 8
LEFT_WRIST = 9
RIGHT_WRIST = 10
LEFT_HIP = 11
RIGHT_HIP = 12
LEFT_KNEE = 13
RIGHT_KNEE = 14
LEFT_ANKLE = 15
RIGHT_ANKLE = 16

NUM_KEYPOINTS = 17


# Skeleton edges for drawing — pairs of keypoint indices
SKELETON_EDGES = [
    (LEFT_SHOULDER, RIGHT_SHOULDER),
    (LEFT_SHOULDER, LEFT_ELBOW), (LEFT_ELBOW, LEFT_WRIST),
    (RIGHT_SHOULDER, RIGHT_ELBOW), (RIGHT_ELBOW, RIGHT_WRIST),
    (LEFT_SHOULDER, LEFT_HIP), (RIGHT_SHOULDER, RIGHT_HIP),
    (LEFT_HIP, RIGHT_HIP),
    (LEFT_HIP, LEFT_KNEE), (LEFT_KNEE, LEFT_ANKLE),
    (RIGHT_HIP, RIGHT_KNEE), (RIGHT_KNEE, RIGHT_ANKLE),
]


@dataclass
class Pose:
    """One detected person.
    keypoints: (17, 3) float array — (x, y, conf). x and y are normalized 0..1
               in the **full camera frame**, not the half-frame.
    bbox: (xmin, ymin, xmax, ymax), normalized.
    score: detection confidence.
    """
    keypoints: np.ndarray  # shape (17, 3), dtype float32
    bbox: tuple[float, float, float, float]
    score: float

    def kp(self, idx: int) -> tuple[float, float, float]:
        """Return (x, y, conf) for one keypoint."""
        x, y, c = self.keypoints[idx]
        return float(x), float(y), float(c)

    @property
    def center_x(self) -> float:
        """Horizontal centroid of the bbox — used to assign player IDs."""
        return 0.5 * (self.bbox[0] + self.bbox[2])

    def to_dict(self) -> dict:
        """Serialize for WebSocket. Returns 17 [x,y,conf] triples."""
        return {
            "keypoints": [[float(x), float(y), float(c)] for x, y, c in self.keypoints],
            "bbox": list(self.bbox),
            "score": float(self.score),
        }
