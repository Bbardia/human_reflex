"""Gesture detection. All gestures are recognized purely from a Pose.

Coordinate system: Pose keypoints are normalized 0..1 in the full camera frame.
Image y goes top-to-bottom, so 'up' means smaller y.
"""
from dataclasses import dataclass, field
from backend.pose.types import (
    Pose, NOSE, LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP,
    LEFT_WRIST, RIGHT_WRIST,
)

CONF_THRESHOLD = 0.3


def _kp_ok(pose: Pose, idx: int) -> bool:
    return bool(pose.keypoints[idx, 2] >= CONF_THRESHOLD)


def is_hands_up(pose: Pose) -> bool:
    """Both wrists above the nose."""
    if not all(_kp_ok(pose, i) for i in (NOSE, LEFT_WRIST, RIGHT_WRIST)):
        return False
    nose_y = pose.keypoints[NOSE, 1]
    lw_y = pose.keypoints[LEFT_WRIST, 1]
    rw_y = pose.keypoints[RIGHT_WRIST, 1]
    return bool(lw_y < nose_y and rw_y < nose_y)


def is_x_arms(pose: Pose) -> bool:
    """Wrists crossed past body midline, both wrists between shoulder.y and hip.y."""
    needed = (LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP, LEFT_WRIST, RIGHT_WRIST)
    if not all(_kp_ok(pose, i) for i in needed):
        return False

    midline_x = 0.5 * (pose.keypoints[LEFT_SHOULDER, 0] + pose.keypoints[RIGHT_SHOULDER, 0])
    chest_top = min(pose.keypoints[LEFT_SHOULDER, 1], pose.keypoints[RIGHT_SHOULDER, 1])
    chest_bot = max(pose.keypoints[LEFT_HIP, 1], pose.keypoints[RIGHT_HIP, 1])

    lw_x, lw_y = pose.keypoints[LEFT_WRIST, 0], pose.keypoints[LEFT_WRIST, 1]
    rw_x, rw_y = pose.keypoints[RIGHT_WRIST, 0], pose.keypoints[RIGHT_WRIST, 1]

    crossed = lw_x > midline_x and rw_x < midline_x
    in_chest_band = chest_top <= lw_y <= chest_bot and chest_top <= rw_y <= chest_bot
    return bool(crossed and in_chest_band)


@dataclass
class GestureHold:
    """Tracks how long a gesture has been continuously active.
    Fires exactly once when the hold threshold is crossed.
    Resets if the gesture goes inactive."""
    hold_ms: int
    _engaged_at_ms: int | None = field(default=None, init=False)
    _has_fired: bool = field(default=False, init=False)

    def update(self, active: bool, now_ms: int) -> bool:
        """Returns True on the frame the hold first crosses the threshold."""
        if not active:
            self._engaged_at_ms = None
            self._has_fired = False
            return False
        if self._engaged_at_ms is None:
            self._engaged_at_ms = now_ms
            return False
        elapsed = now_ms - self._engaged_at_ms
        if elapsed >= self.hold_ms and not self._has_fired:
            self._has_fired = True
            return True
        return False

    def progress(self, now_ms: int) -> float:
        """0..1 fill progress for UI."""
        if self._engaged_at_ms is None:
            return 0.0
        elapsed = now_ms - self._engaged_at_ms
        return max(0.0, min(1.0, elapsed / self.hold_ms))

    def reset(self) -> None:
        self._engaged_at_ms = None
        self._has_fired = False
