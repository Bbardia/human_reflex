import numpy as np
from backend.pose.types import Pose, LEFT_WRIST, RIGHT_WRIST
from backend.games.touch_circle import TouchCircleGame
from backend.config import TouchCircleConfig


def make_pose_with_wrists(left: tuple[float, float], right: tuple[float, float]) -> Pose:
    kps = np.zeros((17, 3), dtype=np.float32)
    kps[LEFT_WRIST] = [left[0], left[1], 1.0]
    kps[RIGHT_WRIST] = [right[0], right[1], 1.0]
    return Pose(keypoints=kps, bbox=(0.0, 0.0, 1.0, 1.0), score=0.9)


# ---- helpers ----

def _config_for_test() -> TouchCircleConfig:
    return TouchCircleConfig(
        rounds=3,
        preroll_ms_min=100,
        preroll_ms_max=100,  # deterministic preroll for tests
        target_size_pct=0.2,
        false_start_speed_threshold=0.5,
        false_start_min_duration_ms=100,
        false_start_penalty_ms=2000,
        summary_min_hold_ms=1000,
    )


# ---- tests ----

def test_starts_in_preroll_with_no_target():
    g = TouchCircleGame(now_ms=0, config=_config_for_test(), seed=1)
    g.tick(0, None, None)
    s = g.to_dict()
    assert s["phase"] == "preroll"
    assert s["target"] is None
    assert s["round"] == 1


def test_target_appears_after_preroll():
    g = TouchCircleGame(now_ms=0, config=_config_for_test(), seed=1)
    g.tick(50, None, None)
    assert g.to_dict()["phase"] == "preroll"
    g.tick(101, None, None)
    s = g.to_dict()
    assert s["phase"] == "active"
    assert s["target"] is not None
    assert 0.0 < s["target"]["x"] < 1.0
    assert 0.0 < s["target"]["y"] < 1.0


def test_p1_hit_records_reaction_time():
    g = TouchCircleGame(now_ms=0, config=_config_for_test(), seed=1)
    g.tick(0, None, None)
    g.tick(101, None, None)  # target spawns
    target = g.to_dict()["target"]
    # P1's wrist on the target (target x is in player-half coords; full-frame x for P1 = target.x * 0.5)
    p1_full_x = target["x"] * 0.5
    p2_full_x = 0.5 + target["x"] * 0.5
    p1 = make_pose_with_wrists(left=(p1_full_x, target["y"]), right=(0.1, 0.1))
    p2 = make_pose_with_wrists(left=(p2_full_x, 0.9), right=(0.9, 0.9))
    # Hit at 350ms (250ms reaction)
    g.tick(351, p1, p2)
    s = g.to_dict()
    last_result = s["results"][-1]
    assert last_result["p1_time_ms"] == 250
    assert last_result["p2_time_ms"] is None  # not yet


def test_round_advances_when_both_have_hit():
    g = TouchCircleGame(now_ms=0, config=_config_for_test(), seed=1)
    g.tick(0, None, None)
    g.tick(101, None, None)
    target = g.to_dict()["target"]
    p1_x = target["x"] * 0.5
    p2_x = 0.5 + target["x"] * 0.5
    p1 = make_pose_with_wrists(left=(p1_x, target["y"]), right=(0.1, 0.1))
    p2 = make_pose_with_wrists(left=(p2_x, target["y"]), right=(0.9, 0.9))
    g.tick(300, p1, None)   # P1 hits (reaction = 199 ms)
    g.tick(450, None, p2)   # P2 hits (reaction = 349 ms)
    # Now we should advance: phase = preroll for round 2
    s = g.to_dict()
    assert s["round"] == 2
    assert s["phase"] == "preroll"


def test_false_start_penalty_when_p1_moves_during_preroll():
    # Use a longer pre-roll and shorter false-start threshold so the timing is unambiguous.
    cfg = TouchCircleConfig(
        rounds=3,
        preroll_ms_min=500,
        preroll_ms_max=500,
        target_size_pct=0.2,
        false_start_speed_threshold=0.5,
        false_start_min_duration_ms=50,
        false_start_penalty_ms=2000,
        summary_min_hold_ms=1000,
    )
    g = TouchCircleGame(now_ms=0, config=cfg, seed=1)
    # Move P1's wrist back and forth fast during pre-roll
    p_a = make_pose_with_wrists(left=(0.1, 0.5), right=(0.1, 0.5))
    p_b = make_pose_with_wrists(left=(0.4, 0.5), right=(0.1, 0.5))
    g.tick(10, p_a, None)   # first sample, no speed yet
    g.tick(20, p_b, None)   # fast motion starts here, started_ms=20
    g.tick(40, p_a, None)
    g.tick(60, p_b, None)
    g.tick(80, p_b, None)   # duration now 60 ms, >= 50 ms threshold → penalty fires
    s = g.to_dict()
    last = s["results"][-1]
    assert last["p1_false_start"] is True
    assert last["p1_time_ms"] == 2000


def test_game_done_after_all_rounds():
    cfg = _config_for_test()  # rounds=3
    g = TouchCircleGame(now_ms=0, config=cfg, seed=1)
    now = 0
    for _round in range(cfg.rounds):
        # advance through preroll
        g.tick(now, None, None)
        now += cfg.preroll_ms_max + 10
        g.tick(now, None, None)
        target = g.to_dict()["target"]
        p1_x = target["x"] * 0.5
        p2_x = 0.5 + target["x"] * 0.5
        p1 = make_pose_with_wrists(left=(p1_x, target["y"]), right=(0.1, 0.1))
        p2 = make_pose_with_wrists(left=(p2_x, target["y"]), right=(0.9, 0.9))
        now += 200
        g.tick(now, p1, p2)
    assert g.is_done() is True
    assert g.winner() in (1, 2, None)


def test_winner_is_lowest_avg_reaction():
    cfg = _config_for_test()
    g = TouchCircleGame(now_ms=0, config=cfg, seed=1)
    now = 0
    for _round in range(cfg.rounds):
        g.tick(now, None, None)
        now += cfg.preroll_ms_max + 10
        g.tick(now, None, None)
        target = g.to_dict()["target"]
        p1_x = target["x"] * 0.5
        p2_x = 0.5 + target["x"] * 0.5
        p1 = make_pose_with_wrists(left=(p1_x, target["y"]), right=(0.1, 0.1))
        p2 = make_pose_with_wrists(left=(p2_x, target["y"]), right=(0.9, 0.9))
        # P1 reacts in 200 ms, P2 in 400 ms
        now_p1 = now + 200
        now_p2 = now + 400
        g.tick(now_p1, p1, None)
        g.tick(now_p2, None, p2)
        now = now_p2 + 1
    assert g.winner() == 1


def test_both_players_false_start_same_round():
    cfg = TouchCircleConfig(
        rounds=3,
        preroll_ms_min=500,
        preroll_ms_max=500,
        target_size_pct=0.2,
        false_start_speed_threshold=0.5,
        false_start_min_duration_ms=50,
        false_start_penalty_ms=2000,
        summary_min_hold_ms=1000,
    )
    g = TouchCircleGame(now_ms=0, config=cfg, seed=1)
    p_a = make_pose_with_wrists(left=(0.1, 0.5), right=(0.9, 0.5))
    p_b = make_pose_with_wrists(left=(0.4, 0.5), right=(0.6, 0.5))
    # Both players move their wrists fast back-and-forth during pre-roll
    # First sample stamps last_xy, second triggers fast-motion start, then
    # we need >= 50 ms more to clear the duration threshold.
    g.tick(10, p_a, p_a)   # baseline
    g.tick(20, p_b, p_b)   # fast motion stamps started=20 for both
    g.tick(40, p_a, p_a)   # still fast
    g.tick(60, p_b, p_b)   # still fast
    g.tick(80, p_a, p_a)   # duration = 60 ms >= 50 ms → penalty fires for both
    s = g.to_dict()
    last = s["results"][-1]
    assert last["p1_false_start"] is True
    assert last["p2_false_start"] is True
    assert last["p1_time_ms"] == 2000
    assert last["p2_time_ms"] == 2000


def test_tick_after_done_is_noop():
    cfg = _config_for_test()  # rounds=3
    g = TouchCircleGame(now_ms=0, config=cfg, seed=1)
    now = 0
    for _round in range(cfg.rounds):
        g.tick(now, None, None)
        now += cfg.preroll_ms_max + 10
        g.tick(now, None, None)
        target = g.to_dict()["target"]
        p1_x = target["x"] * 0.5
        p2_x = 0.5 + target["x"] * 0.5
        p1 = make_pose_with_wrists(left=(p1_x, target["y"]), right=(0.1, 0.1))
        p2 = make_pose_with_wrists(left=(p2_x, target["y"]), right=(0.9, 0.9))
        now += 200
        g.tick(now, p1, p2)
    assert g.is_done() is True
    snapshot_before = g.to_dict()
    # Tick again — should not advance round, change phase, or alter results
    g.tick(now + 10000, p1, p2)
    snapshot_after = g.to_dict()
    assert snapshot_before == snapshot_after


def test_winner_when_p2_never_present():
    cfg = _config_for_test()
    g = TouchCircleGame(now_ms=0, config=cfg, seed=1)
    # Drive P1 only — P2 is None for the entire game. Game can't end this way
    # because round-advance requires both result.p1_time_ms and p2_time_ms set.
    # So we drive P1 hits to populate p1_time_ms, then leave p2_time_ms None,
    # then force the game to done by exhausting rounds via direct phase poke.
    # That's not realistic in normal play but tests winner() math when p2
    # average time = inf.
    now = 0
    for _round in range(cfg.rounds):
        g.tick(now, None, None)
        now += cfg.preroll_ms_max + 10
        g.tick(now, None, None)
        target = g.to_dict()["target"]
        p1_x = target["x"] * 0.5
        p1 = make_pose_with_wrists(left=(p1_x, target["y"]), right=(0.1, 0.1))
        # Hit P1; manually mark P2 time so round advances (penalty-style)
        now += 200
        g.tick(now, p1, None)
        # Force p2 result to a sentinel so the round can advance — simulating
        # what happens if P2 never moves and the game eventually times out.
        # Instead, mark P2 false-start to settle the round. Easiest: re-use
        # the false-start penalty path indirectly by setting result manually.
        last = g._results[-1]  # type: ignore[attr-defined]
        last.p2_time_ms = None  # P2 truly never present
        # Round won't advance by itself. Force advance for test purposes:
        g._advance_round(now)  # type: ignore[attr-defined]
        now += 1
    assert g.is_done() is True
    # P1 has finite avg, P2 has inf → P1 wins
    assert g.winner() == 1
