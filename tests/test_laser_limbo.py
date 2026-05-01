import numpy as np
from backend.config import LaserLimboConfig
from backend.games.laser_limbo import LaserLimboGame, _Laser
from backend.pose.types import (
    Pose, NUM_KEYPOINTS, NOSE,
)


def make_pose(positions: dict[int, tuple[float, float]]) -> Pose:
    """Build a Pose with the listed keypoints set; the rest stay at conf=0."""
    kps = np.zeros((17, 3), dtype=np.float32)
    for idx, (x, y) in positions.items():
        kps[idx] = [x, y, 1.0]
    return Pose(keypoints=kps, bbox=(0.0, 0.0, 1.0, 1.0), score=0.9)


def standing_pose_at(x_full_frame: float = 0.25) -> Pose:
    """A simple pose with all 17 keypoints at the same x, varying y."""
    kps = np.zeros((17, 3), dtype=np.float32)
    for i in range(17):
        kps[i] = [x_full_frame, 0.4 + 0.02 * (i - 8), 1.0]  # spread vertically near 0.4
    return Pose(keypoints=kps, bbox=(0.0, 0.0, 1.0, 1.0), score=0.9)


def _config_for_test() -> LaserLimboConfig:
    return LaserLimboConfig(
        match_duration_s=2.0,  # short match for tests
        starting_hp=3,
        rate_hz_early=10.0,
        rate_hz_late=20.0,
        ramp_at_s=1.0,
        laser_duration_ms=200,
        laser_thickness=0.05,
        invuln_ms=200,
        resolve_hold_ms=100,
    )


# ---- _Laser unit tests ----

def test_horizontal_laser_position_at_endpoints():
    cfg = _config_for_test()
    laser = _Laser(
        spawn_ms=1000, duration_ms=cfg.laser_duration_ms,
        orientation="h", direction=+1, thickness=cfg.laser_thickness,
    )
    # At spawn time, position should be at start (just above frame: -thickness)
    pos_start = laser.position(1000)
    assert pos_start is not None
    assert pos_start <= 0.0  # entered from above
    # At end, position should be just below frame
    pos_end = laser.position(1000 + cfg.laser_duration_ms - 1)
    assert pos_end is not None
    assert pos_end >= 1.0
    # Past duration, no position
    assert laser.position(1000 + cfg.laser_duration_ms + 10) is None


def test_horizontal_laser_hits_keypoint_in_path():
    cfg = _config_for_test()
    # Horizontal laser, spawning at t=0, sweeps top→bottom over 200ms
    laser = _Laser(
        spawn_ms=0, duration_ms=200,
        orientation="h", direction=+1, thickness=0.05,
    )
    # At t=100ms, laser is at midpoint y ≈ 0.5
    # Pose with a keypoint at y=0.5 should be a hit
    pose = make_pose({NOSE: (0.25, 0.5)})  # P1 nose at y=0.5
    assert laser.hits(pose, player_idx=1, now_ms=100) is True
    # Pose with all keypoints far from y=0.5 should not be a hit
    pose_clear = make_pose({NOSE: (0.25, 0.9)})
    assert laser.hits(pose_clear, player_idx=1, now_ms=100) is False


def test_vertical_laser_uses_half_frame_x():
    laser = _Laser(
        spawn_ms=0, duration_ms=200,
        orientation="v", direction=+1, thickness=0.05,
    )
    # At t=100ms, vertical laser at x ≈ 0.5 of HALF-frame.
    # For P1 (full-frame 0..0.5), half_x of full_x=0.25 is 0.5 → hit.
    pose_p1 = make_pose({NOSE: (0.25, 0.5)})
    assert laser.hits(pose_p1, player_idx=1, now_ms=100) is True
    # For P2 (full-frame 0.5..1), half_x of full_x=0.75 is 0.5 → hit.
    pose_p2 = make_pose({NOSE: (0.75, 0.5)})
    assert laser.hits(pose_p2, player_idx=2, now_ms=100) is True
    # P1 with keypoint outside its half should not hit (full_x=0.75 → half_x=1.5 OOB).
    pose_oob = make_pose({NOSE: (0.75, 0.5)})
    assert laser.hits(pose_oob, player_idx=1, now_ms=100) is False


# ---- Game state machine tests ----

def test_starts_active_with_full_hp():
    cfg = _config_for_test()
    g = LaserLimboGame(now_ms=0, config=cfg, seed=1)
    g.tick(0, None, None)
    s = g.to_dict()
    assert s["phase"] == "active"
    assert s["p1_hp"] == cfg.starting_hp
    assert s["p2_hp"] == cfg.starting_hp


def test_lasers_spawn_over_time():
    cfg = _config_for_test()
    g = LaserLimboGame(now_ms=0, config=cfg, seed=1)
    # Run for 500ms; with rate_hz_early=10, expect ~5 lasers spawned
    for t in range(0, 600, 10):
        g.tick(t, None, None)
    s = g.to_dict()
    assert len(s["lasers"]) > 0  # at least one laser active or expired in the window


def test_player_takes_damage_on_collision():
    cfg = _config_for_test()
    g = LaserLimboGame(now_ms=0, config=cfg, seed=1)
    # Force-spawn a horizontal laser at a known position via private API
    g._spawn_laser(now_ms=0)  # type: ignore[attr-defined]
    laser = g._active_lasers[0]  # type: ignore[attr-defined]
    # Standing in laser's path
    p1 = standing_pose_at(0.25)  # P1 at x=0.25 — within P1's half
    p2 = make_pose({NOSE: (1.5, 1.5)})  # P2 way out of frame
    # Tick through laser's lifetime; P1 must intersect the line at some point
    initial_hp = g.to_dict()["p1_hp"]
    for t in range(0, laser.duration_ms + 10, 10):
        g.tick(t, p1, p2)
    assert g.to_dict()["p1_hp"] < initial_hp
    assert g.to_dict()["p2_hp"] == cfg.starting_hp


def test_invuln_prevents_double_hit():
    cfg = _config_for_test()
    g = LaserLimboGame(now_ms=0, config=cfg, seed=1)
    g._spawn_laser(now_ms=0)  # type: ignore[attr-defined]
    p1 = standing_pose_at(0.25)
    # Spawn another laser at the same time
    g._spawn_laser(now_ms=0)  # type: ignore[attr-defined]
    # Tick once at midpoint when both lasers should hit
    g.tick(100, p1, None)
    # Despite two simultaneous lasers, only one HP lost (invuln after the first)
    assert g.to_dict()["p1_hp"] == cfg.starting_hp - 1


def test_game_ends_at_match_duration():
    cfg = _config_for_test()
    g = LaserLimboGame(now_ms=0, config=cfg, seed=1)
    # Drive past match_duration + resolve_hold
    end_ms = int(cfg.match_duration_s * 1000) + cfg.resolve_hold_ms + 100
    for t in range(0, end_ms + 100, 50):
        g.tick(t, None, None)
    assert g.is_done() is True


def test_game_ends_when_both_zero_hp():
    cfg = _config_for_test()
    g = LaserLimboGame(now_ms=0, config=cfg, seed=1)
    # Manually set both HPs to 0
    g._p1_hp = 0  # type: ignore[attr-defined]
    g._p2_hp = 0  # type: ignore[attr-defined]
    g.tick(100, None, None)
    g.tick(100 + cfg.resolve_hold_ms + 50, None, None)
    assert g.is_done() is True


def test_winner_is_higher_hp_at_end():
    cfg = _config_for_test()
    g = LaserLimboGame(now_ms=0, config=cfg, seed=1)
    # P1 starts with 2 HP, P2 with 1 HP
    g._p1_hp = 2  # type: ignore[attr-defined]
    g._p2_hp = 1  # type: ignore[attr-defined]
    end_ms = int(cfg.match_duration_s * 1000) + cfg.resolve_hold_ms + 100
    for t in range(0, end_ms + 100, 50):
        g.tick(t, None, None)
    assert g.winner() == 1


def test_winner_tiebreak_fewer_hits():
    cfg = _config_for_test()
    g = LaserLimboGame(now_ms=0, config=cfg, seed=1)
    g._p1_hp = 2  # type: ignore[attr-defined]
    g._p2_hp = 2  # type: ignore[attr-defined]
    g._p1_hits = 1  # type: ignore[attr-defined]
    g._p2_hits = 3  # type: ignore[attr-defined]
    end_ms = int(cfg.match_duration_s * 1000) + cfg.resolve_hold_ms + 100
    for t in range(0, end_ms + 100, 50):
        g.tick(t, None, None)
    assert g.winner() == 1


def test_summary_shape():
    cfg = _config_for_test()
    g = LaserLimboGame(now_ms=0, config=cfg, seed=1)
    end_ms = int(cfg.match_duration_s * 1000) + cfg.resolve_hold_ms + 100
    for t in range(0, end_ms + 100, 50):
        g.tick(t, None, None)
    s = g.summary()
    assert s["name"] == "Laser Limbo"
    assert s["metric_unit"] == "HP"
    assert s["winner"] in (1, 2, None)
    assert "p1_metric" in s and "p2_metric" in s
