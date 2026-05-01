import numpy as np
from backend.pose.types import Pose, NOSE, LEFT_WRIST, RIGHT_WRIST
from backend.session import Session


def hands_up_pose() -> Pose:
    kps = np.zeros((17, 3), dtype=np.float32)
    kps[NOSE] = [0.5, 0.4, 1.0]
    kps[LEFT_WRIST] = [0.4, 0.1, 1.0]
    kps[RIGHT_WRIST] = [0.6, 0.1, 1.0]
    return Pose(keypoints=kps, bbox=(0.2, 0.0, 0.8, 1.0), score=0.9)


def neutral_pose() -> Pose:
    kps = np.zeros((17, 3), dtype=np.float32)
    kps[NOSE] = [0.5, 0.4, 1.0]
    kps[LEFT_WRIST] = [0.4, 0.7, 1.0]
    kps[RIGHT_WRIST] = [0.6, 0.7, 1.0]
    return Pose(keypoints=kps, bbox=(0.2, 0.0, 0.8, 1.0), score=0.9)


def test_starts_on_title_screen():
    s = Session(now_ms=0)
    s.tick(now_ms=0, p1=None, p2=None)
    assert s.to_dict(0)["screen"] == "title"


def test_p1_hands_up_2s_starts_countdown():
    s = Session(now_ms=0)
    p1 = hands_up_pose()
    p2 = neutral_pose()
    # Hands held for 2 seconds — at frame 2001 ms the gesture fires
    for t in range(0, 2100, 50):
        s.tick(now_ms=t, p1=p1, p2=p2)
    assert s.to_dict(0)["screen"] == "countdown"


def test_countdown_advances_to_game():
    s = Session(now_ms=0)
    p1 = hands_up_pose()
    p2 = neutral_pose()
    for t in range(0, 2100, 50):
        s.tick(now_ms=t, p1=p1, p2=p2)
    # Now in countdown. Wait 4 seconds for it to finish.
    for t in range(2100, 6500, 50):
        s.tick(now_ms=t, p1=neutral_pose(), p2=neutral_pose())
    assert s.to_dict(0)["screen"] == "game"


def test_game_completion_advances_to_summary():
    s = Session(now_ms=0)
    # Crank through to game start
    p1 = hands_up_pose()
    p2 = neutral_pose()
    for t in range(0, 2100, 50):
        s.tick(now_ms=t, p1=p1, p2=p2)
    for t in range(2100, 6500, 50):
        s.tick(now_ms=t, p1=neutral_pose(), p2=neutral_pose())
    assert s.to_dict(0)["screen"] == "game"
    # Force the inner game to be done
    s._game._phase = "done"  # type: ignore[attr-defined]
    s.tick(now_ms=6600, p1=neutral_pose(), p2=neutral_pose())
    assert s.to_dict(0)["screen"] == "summary"


def test_summary_returns_to_title_after_hands_up():
    s = Session(now_ms=0)
    s._enter_summary(now_ms=0, summary={"name": "x", "winner": 1})  # type: ignore[attr-defined]
    p1 = hands_up_pose()
    p2 = neutral_pose()
    # Hold hands up for 2.1 seconds AFTER the brief auto-hold delay
    for t in range(1000, 4100, 50):
        s.tick(now_ms=t, p1=p1, p2=p2)
    assert s.to_dict(0)["screen"] == "title"
