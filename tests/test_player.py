import numpy as np
import pytest
from backend.pose.types import Pose
from backend.player import PlayerRouter


def make_pose(center_x: float, score: float = 0.9) -> Pose:
    bbox = (center_x - 0.1, 0.1, center_x + 0.1, 0.9)
    return Pose(keypoints=np.zeros((17, 3), dtype=np.float32), bbox=bbox, score=score)


def test_assigns_leftmost_to_p1_rightmost_to_p2():
    router = PlayerRouter()
    p_left = make_pose(0.25)
    p_right = make_pose(0.75)
    p1, p2 = router.route([p_left, p_right])
    assert p1 is p_left
    assert p2 is p_right


def test_assigns_correctly_when_input_order_is_reversed():
    router = PlayerRouter()
    p_left = make_pose(0.25)
    p_right = make_pose(0.75)
    p1, p2 = router.route([p_right, p_left])
    assert p1 is p_left
    assert p2 is p_right


def test_returns_none_for_missing_player():
    router = PlayerRouter()
    only_left = make_pose(0.3)
    p1, p2 = router.route([only_left])
    assert p1 is only_left
    assert p2 is None

    p1, p2 = router.route([])
    assert p1 is None
    assert p2 is None


def test_takes_two_largest_when_more_than_two_detected():
    router = PlayerRouter()
    big_left = make_pose(0.25)
    big_right = make_pose(0.75)
    # smaller bbox => smaller area
    small_intruder = Pose(
        keypoints=np.zeros((17, 3), dtype=np.float32),
        bbox=(0.45, 0.4, 0.55, 0.6),  # tiny
        score=0.9,
    )
    p1, p2 = router.route([small_intruder, big_left, big_right])
    assert p1 is big_left
    assert p2 is big_right
