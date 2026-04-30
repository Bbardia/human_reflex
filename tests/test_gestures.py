import numpy as np
from backend.pose.types import (
    Pose, NOSE, LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP,
    LEFT_WRIST, RIGHT_WRIST,
)
from backend.gestures import is_hands_up, is_x_arms, GestureHold


def make_pose(positions: dict[int, tuple[float, float]]) -> Pose:
    """Build a Pose with given (x, y) for selected keypoints, conf=1.0 each."""
    kps = np.zeros((17, 3), dtype=np.float32)
    for idx, (x, y) in positions.items():
        kps[idx] = [x, y, 1.0]
    return Pose(keypoints=kps, bbox=(0.0, 0.0, 1.0, 1.0), score=0.9)


def test_hands_up_true_when_both_wrists_above_nose():
    pose = make_pose({
        NOSE: (0.5, 0.3),
        LEFT_WRIST: (0.4, 0.1),
        RIGHT_WRIST: (0.6, 0.1),
    })
    assert is_hands_up(pose) is True


def test_hands_up_false_when_only_one_wrist_up():
    pose = make_pose({
        NOSE: (0.5, 0.3),
        LEFT_WRIST: (0.4, 0.1),   # up
        RIGHT_WRIST: (0.6, 0.5),  # down
    })
    assert is_hands_up(pose) is False


def test_hands_up_false_with_low_confidence():
    pose = make_pose({
        NOSE: (0.5, 0.3),
        LEFT_WRIST: (0.4, 0.1),
        RIGHT_WRIST: (0.6, 0.1),
    })
    pose.keypoints[LEFT_WRIST, 2] = 0.1  # tank confidence
    assert is_hands_up(pose) is False


def test_x_arms_true_when_wrists_cross_midline_at_chest_height():
    pose = make_pose({
        LEFT_SHOULDER: (0.4, 0.3),
        RIGHT_SHOULDER: (0.6, 0.3),
        LEFT_HIP: (0.4, 0.7),
        RIGHT_HIP: (0.6, 0.7),
        LEFT_WRIST: (0.6, 0.5),   # left wrist crossed past midline x=0.5
        RIGHT_WRIST: (0.4, 0.5),  # right wrist crossed past midline
    })
    assert is_x_arms(pose) is True


def test_x_arms_false_when_arms_down():
    pose = make_pose({
        LEFT_SHOULDER: (0.4, 0.3),
        RIGHT_SHOULDER: (0.6, 0.3),
        LEFT_HIP: (0.4, 0.7),
        RIGHT_HIP: (0.6, 0.7),
        LEFT_WRIST: (0.4, 0.9),   # wrists below hips
        RIGHT_WRIST: (0.6, 0.9),
    })
    assert is_x_arms(pose) is False


def test_gesture_hold_fires_after_hold_duration():
    hold = GestureHold(hold_ms=2000)
    # Held for 1000 ms — not enough yet
    assert hold.update(active=True, now_ms=0) is False
    assert hold.update(active=True, now_ms=1000) is False
    assert hold.update(active=True, now_ms=1999) is False
    # Crossed threshold
    assert hold.update(active=True, now_ms=2001) is True
    # Once fired, doesn't fire again until released and re-engaged
    assert hold.update(active=True, now_ms=3000) is False


def test_gesture_hold_progress_value():
    hold = GestureHold(hold_ms=2000)
    hold.update(active=True, now_ms=0)
    hold.update(active=True, now_ms=500)
    assert 0.24 < hold.progress(now_ms=500) < 0.26
    hold.update(active=False, now_ms=1000)
    assert hold.progress(now_ms=1500) == 0.0


def test_gesture_hold_releases_when_inactive():
    hold = GestureHold(hold_ms=2000)
    hold.update(active=True, now_ms=0)
    hold.update(active=True, now_ms=1500)
    hold.update(active=False, now_ms=1600)  # released early
    # Re-engage — must start over
    hold.update(active=True, now_ms=1700)
    assert hold.update(active=True, now_ms=2000) is False
    assert hold.update(active=True, now_ms=3701) is True
