import numpy as np
from backend.config import GoalieConfig
from backend.games.goalie import GoalieGame
from backend.pose.types import (
    Pose, LEFT_WRIST, RIGHT_WRIST, LEFT_ANKLE, RIGHT_ANKLE, NOSE,
)


def make_pose(positions: dict[int, tuple[float, float]]) -> Pose:
    kps = np.zeros((17, 3), dtype=np.float32)
    for idx, (x, y) in positions.items():
        kps[idx] = [x, y, 1.0]
    return Pose(keypoints=kps, bbox=(0.0, 0.0, 1.0, 1.0), score=0.9)


def _config_for_test(shots: int = 3) -> GoalieConfig:
    return GoalieConfig(
        shots=shots,
        preroll_ms_min=100,
        preroll_ms_max=100,
        ball_travel_ms=500,
        resolve_hold_ms=100,
    )


def test_starts_in_preroll_with_no_ball():
    g = GoalieGame(now_ms=0, config=_config_for_test(), seed=1)
    g.tick(0, None, None)
    s = g.to_dict()
    assert s["phase"] == "preroll"
    assert s["ball"] is None
    assert s["shot"] == 1


def test_ball_appears_after_preroll():
    g = GoalieGame(now_ms=0, config=_config_for_test(), seed=1)
    g.tick(50, None, None)
    assert g.to_dict()["phase"] == "preroll"
    g.tick(101, None, None)
    s = g.to_dict()
    assert s["phase"] == "active"
    assert s["ball"] is not None
    assert 0 <= s["ball"]["zone"] <= 4


def test_p1_saves_when_wrist_inside_zone():
    cfg = _config_for_test()
    g = GoalieGame(now_ms=0, config=cfg, seed=1)
    g.tick(0, None, None)
    g.tick(101, None, None)  # ball spawns
    zone_idx = g.to_dict()["ball"]["zone"]
    zmin_x, zmin_y, zmax_x, zmax_y = cfg.zones[zone_idx]
    cx = 0.5 * (zmin_x + zmax_x)
    cy = 0.5 * (zmin_y + zmax_y)
    # P1 wrist at the center of the zone in P1's half (full-frame x = cx * 0.5)
    p1 = make_pose({LEFT_WRIST: (cx * 0.5, cy)})
    p2 = make_pose({})  # no relevant keypoints
    g.tick(250, p1, p2)
    s = g.to_dict()
    last = s["results"][-1]
    assert last["p1_saved"] is True
    assert last["p1_save_time_ms"] == 149  # 250 - 101


def test_p2_saves_with_ankle_in_zone():
    cfg = _config_for_test()
    g = GoalieGame(now_ms=0, config=cfg, seed=1)
    g.tick(0, None, None)
    g.tick(101, None, None)
    zone_idx = g.to_dict()["ball"]["zone"]
    zmin_x, zmin_y, zmax_x, zmax_y = cfg.zones[zone_idx]
    cx = 0.5 * (zmin_x + zmax_x)
    cy = 0.5 * (zmin_y + zmax_y)
    # P2 right-ankle at zone center; P2 full-frame x = 0.5 + cx * 0.5
    p2 = make_pose({RIGHT_ANKLE: (0.5 + cx * 0.5, cy)})
    p1 = make_pose({})
    g.tick(300, p1, p2)
    last = g.to_dict()["results"][-1]
    assert last["p2_saved"] is True
    assert last["p2_save_time_ms"] == 199  # 300 - 101


def test_no_save_when_keypoints_outside_zone():
    cfg = _config_for_test()
    g = GoalieGame(now_ms=0, config=cfg, seed=1)
    g.tick(0, None, None)
    g.tick(101, None, None)
    # Both players idle, hands at sides
    idle = make_pose({
        LEFT_WRIST: (0.05, 0.99),
        RIGHT_WRIST: (0.95, 0.99),
        LEFT_ANKLE: (0.05, 0.99),
        RIGHT_ANKLE: (0.95, 0.99),
        NOSE: (0.5, 0.99),
    })
    # Wait past ball travel + resolve
    g.tick(700, idle, idle)
    g.tick(800, idle, idle)
    last = g.to_dict()["results"][-1]
    assert last["p1_saved"] is False
    assert last["p2_saved"] is False
    assert last["p1_save_time_ms"] is None
    assert last["p2_save_time_ms"] is None


def test_round_advances_after_resolve():
    cfg = _config_for_test()
    g = GoalieGame(now_ms=0, config=cfg, seed=1)
    g.tick(0, None, None)
    g.tick(101, None, None)
    # Wait through ball travel + resolve hold (500 + 100 = 600 from spawn at 101)
    g.tick(800, None, None)
    s = g.to_dict()
    assert s["shot"] == 2
    assert s["phase"] == "preroll"


def test_game_done_after_all_shots():
    cfg = _config_for_test(shots=3)
    g = GoalieGame(now_ms=0, config=cfg, seed=1)
    now = 0
    for _ in range(cfg.shots):
        g.tick(now, None, None)
        now += cfg.preroll_ms_max + 10  # +110 → ball spawns
        g.tick(now, None, None)
        now += cfg.ball_travel_ms + cfg.resolve_hold_ms + 50  # past resolve
        g.tick(now, None, None)
    assert g.is_done() is True


def test_winner_is_player_with_more_saves():
    cfg = _config_for_test(shots=3)
    g = GoalieGame(now_ms=0, config=cfg, seed=1)
    now = 0
    for shot_idx in range(cfg.shots):
        g.tick(now, None, None)
        now += cfg.preroll_ms_max + 10
        g.tick(now, None, None)
        zone_idx = g.to_dict()["ball"]["zone"]
        zmin_x, zmin_y, zmax_x, zmax_y = cfg.zones[zone_idx]
        cx = 0.5 * (zmin_x + zmax_x)
        cy = 0.5 * (zmin_y + zmax_y)
        # P1 always saves; P2 only saves the first shot
        p1 = make_pose({LEFT_WRIST: (cx * 0.5, cy)})
        if shot_idx == 0:
            p2 = make_pose({LEFT_WRIST: (0.5 + cx * 0.5, cy)})
        else:
            p2 = make_pose({LEFT_WRIST: (0.99, 0.99)})
        g.tick(now + 200, p1, p2)
        # Wait past resolve
        now += cfg.ball_travel_ms + cfg.resolve_hold_ms + 50
        g.tick(now, None, None)
    assert g.winner() == 1


def test_summary_shape():
    cfg = _config_for_test(shots=3)
    g = GoalieGame(now_ms=0, config=cfg, seed=1)
    now = 0
    for _ in range(cfg.shots):
        g.tick(now, None, None)
        now += cfg.preroll_ms_max + 10
        g.tick(now, None, None)
        now += cfg.ball_travel_ms + cfg.resolve_hold_ms + 50
        g.tick(now, None, None)
    s = g.summary()
    assert s["name"] == "Goalie"
    assert "p1_metric" in s and "p2_metric" in s
    assert s["metric_unit"] == "saves"
    assert s["winner"] in (1, 2, None)
