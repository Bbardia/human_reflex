import numpy as np
from backend.config import CONFIG
from backend.pose.types import Pose, NOSE, LEFT_WRIST, RIGHT_WRIST
from backend.session import (
    Session, GAME_REGISTRY,
    SCREEN_TITLE, SCREEN_COUNTDOWN, SCREEN_GAME,
    SCREEN_INTERMISSION, SCREEN_LEADERBOARD,
)


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


def test_starts_on_title():
    s = Session(now_ms=0)
    s.tick(now_ms=0, p1=None, p2=None)
    assert s.to_dict(0)["screen"] == SCREEN_TITLE


def test_p1_hands_up_starts_countdown():
    s = Session(now_ms=0)
    p1 = hands_up_pose()
    p2 = neutral_pose()
    for t in range(0, 2100, 50):
        s.tick(now_ms=t, p1=p1, p2=p2)
    assert s.to_dict(2100)["screen"] == SCREEN_COUNTDOWN


def test_countdown_advances_to_first_game():
    s = Session(now_ms=0)
    p1 = hands_up_pose()
    p2 = neutral_pose()
    for t in range(0, 2100, 50):
        s.tick(now_ms=t, p1=p1, p2=p2)
    for t in range(2100, 6500, 50):
        s.tick(now_ms=t, p1=neutral_pose(), p2=neutral_pose())
    snap = s.to_dict(6500)
    assert snap["screen"] == SCREEN_GAME
    # First game in registry is Touch the Circle
    assert snap["game"]["type"] == "touch_circle"


def test_first_game_completion_advances_to_intermission():
    s = Session(now_ms=0)
    s._enter_game(0)  # type: ignore[attr-defined]
    s._game._phase = "done"  # type: ignore[union-attr]
    s.tick(now_ms=100, p1=None, p2=None)
    assert s.to_dict(100)["screen"] == SCREEN_INTERMISSION


def test_intermission_auto_advances_to_countdown():
    s = Session(now_ms=0)
    s._enter_intermission(0, {"name": "Test", "winner": 1, "p1_metric": 1, "p2_metric": 0, "metric_unit": "x"})  # type: ignore[attr-defined]
    auto_ms = CONFIG.session.intermission_ms
    s.tick(now_ms=auto_ms + 1, p1=neutral_pose(), p2=neutral_pose())
    assert s.to_dict(auto_ms + 1)["screen"] == SCREEN_COUNTDOWN


def test_intermission_hands_up_advances_early():
    s = Session(now_ms=0)
    s._enter_intermission(0, {"name": "Test", "winner": 1, "p1_metric": 1, "p2_metric": 0, "metric_unit": "x"})  # type: ignore[attr-defined]
    p1 = hands_up_pose()
    p2 = neutral_pose()
    for t in range(0, 2100, 50):
        s.tick(now_ms=t, p1=p1, p2=p2)
    assert s.to_dict(2100)["screen"] == SCREEN_COUNTDOWN


def test_last_game_completion_advances_to_leaderboard():
    s = Session(now_ms=0)
    # Force into the last game
    s._game_index = len(GAME_REGISTRY) - 2  # type: ignore[attr-defined]
    s._enter_game(0)  # advances index to last
    s._game._phase = "done"  # type: ignore[union-attr]
    # Stub the summary so leaderboard math can run
    s._game.summary = lambda: {"name": "X", "winner": 1, "p1_metric": 1, "p2_metric": 0, "metric_unit": "x"}  # type: ignore[union-attr]
    s.tick(now_ms=100, p1=None, p2=None)
    snap = s.to_dict(100)
    assert snap["screen"] == SCREEN_LEADERBOARD
    assert "leaderboard" in snap


def test_leaderboard_overall_winner_by_game_wins():
    s = Session(now_ms=0)
    s._screen = SCREEN_LEADERBOARD  # type: ignore[attr-defined]
    s._completed_summaries = [  # type: ignore[attr-defined]
        {"name": "G1", "winner": 1, "p1_metric": 1, "p2_metric": 0, "metric_unit": "x"},
        {"name": "G2", "winner": 1, "p1_metric": 5, "p2_metric": 4, "metric_unit": "y"},
    ]
    snap = s.to_dict(0)
    lb = snap["leaderboard"]
    assert lb["winner"] == 1
    assert lb["p1_wins"] == 2
    assert lb["p2_wins"] == 0
    assert len(lb["games"]) == 2


def test_leaderboard_draw_when_tied():
    s = Session(now_ms=0)
    s._screen = SCREEN_LEADERBOARD  # type: ignore[attr-defined]
    s._completed_summaries = [  # type: ignore[attr-defined]
        {"name": "G1", "winner": 1, "p1_metric": 1, "p2_metric": 0, "metric_unit": "x"},
        {"name": "G2", "winner": 2, "p1_metric": 0, "p2_metric": 5, "metric_unit": "y"},
    ]
    snap = s.to_dict(0)
    assert snap["leaderboard"]["winner"] is None


def test_leaderboard_returns_to_title_after_hands_up():
    s = Session(now_ms=0)
    s._screen = SCREEN_LEADERBOARD  # type: ignore[attr-defined]
    s._screen_entered_ms = 0  # type: ignore[attr-defined]
    p1 = hands_up_pose()
    p2 = neutral_pose()
    # Hold past the min-hold-ms then hold for 2s
    for t in range(1500, 4100, 50):
        s.tick(now_ms=t, p1=p1, p2=p2)
    assert s.to_dict(4100)["screen"] == SCREEN_TITLE
