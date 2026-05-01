import numpy as np
from backend.config import PoseSimonConfig
from backend.games.pose_simon import (
    PoseSimonGame, TARGET_POSES,
    is_arms_up, is_t_pose, is_left_arm_up, is_right_arm_up,
    is_hands_on_hips, is_squat,
)
from backend.pose.types import (
    Pose, NOSE, LEFT_SHOULDER, RIGHT_SHOULDER,
    LEFT_HIP, RIGHT_HIP, LEFT_KNEE, RIGHT_KNEE,
    LEFT_WRIST, RIGHT_WRIST,
)


def make_pose(positions: dict[int, tuple[float, float]]) -> Pose:
    kps = np.zeros((17, 3), dtype=np.float32)
    for idx, (x, y) in positions.items():
        kps[idx] = [x, y, 1.0]
    return Pose(keypoints=kps, bbox=(0.0, 0.0, 1.0, 1.0), score=0.9)


# ---- Pose detector unit tests ----

def test_arms_up_detector():
    yes = make_pose({NOSE: (0.5, 0.4), LEFT_WRIST: (0.4, 0.1), RIGHT_WRIST: (0.6, 0.1)})
    assert is_arms_up(yes) is True
    no = make_pose({NOSE: (0.5, 0.4), LEFT_WRIST: (0.4, 0.5), RIGHT_WRIST: (0.6, 0.5)})
    assert is_arms_up(no) is False


def test_t_pose_detector():
    cfg = PoseSimonConfig()
    # Shoulders at (0.4, 0.3) and (0.6, 0.3); shoulder-width = 0.2.
    # x_factor=1.2 so wrists must be > 0.24 away from their shoulder horizontally.
    # Place left wrist at (0.1, 0.3) → 0.3 from left shoulder ✓
    # Place right wrist at (0.9, 0.3) → 0.3 from right shoulder ✓
    yes = make_pose({
        LEFT_SHOULDER: (0.4, 0.3), RIGHT_SHOULDER: (0.6, 0.3),
        LEFT_WRIST: (0.1, 0.3), RIGHT_WRIST: (0.9, 0.3),
    })
    assert is_t_pose(yes, cfg) is True
    no = make_pose({
        LEFT_SHOULDER: (0.4, 0.3), RIGHT_SHOULDER: (0.6, 0.3),
        LEFT_WRIST: (0.4, 0.7), RIGHT_WRIST: (0.6, 0.7),  # arms down
    })
    assert is_t_pose(no, cfg) is False


def test_left_arm_up_detector():
    # Anatomical LEFT (image-left, low x with mirroring at capture)
    yes = make_pose({
        NOSE: (0.5, 0.4),
        LEFT_SHOULDER: (0.4, 0.3), RIGHT_SHOULDER: (0.6, 0.3),
        LEFT_WRIST: (0.4, 0.1),    # above nose
        RIGHT_WRIST: (0.6, 0.6),   # below shoulders
    })
    assert is_left_arm_up(yes) is True
    no_both_up = make_pose({
        NOSE: (0.5, 0.4),
        LEFT_SHOULDER: (0.4, 0.3), RIGHT_SHOULDER: (0.6, 0.3),
        LEFT_WRIST: (0.4, 0.1), RIGHT_WRIST: (0.6, 0.1),  # both up
    })
    assert is_left_arm_up(no_both_up) is False


def test_right_arm_up_detector():
    yes = make_pose({
        NOSE: (0.5, 0.4),
        LEFT_SHOULDER: (0.4, 0.3), RIGHT_SHOULDER: (0.6, 0.3),
        RIGHT_WRIST: (0.6, 0.1),   # above nose
        LEFT_WRIST: (0.4, 0.6),    # below shoulders
    })
    assert is_right_arm_up(yes) is True


def test_hands_on_hips_detector():
    cfg = PoseSimonConfig()
    yes = make_pose({
        LEFT_HIP: (0.4, 0.7), RIGHT_HIP: (0.6, 0.7),
        LEFT_WRIST: (0.42, 0.72),  # close to left hip
        RIGHT_WRIST: (0.58, 0.72),  # close to right hip
    })
    assert is_hands_on_hips(yes, cfg) is True
    no = make_pose({
        LEFT_HIP: (0.4, 0.7), RIGHT_HIP: (0.6, 0.7),
        LEFT_WRIST: (0.4, 0.2), RIGHT_WRIST: (0.6, 0.2),  # arms up, not on hips
    })
    assert is_hands_on_hips(no, cfg) is False


def test_squat_detector():
    yes = make_pose({
        LEFT_HIP: (0.4, 0.6), RIGHT_HIP: (0.6, 0.6),
        LEFT_KNEE: (0.4, 0.5), RIGHT_KNEE: (0.6, 0.5),  # knees ABOVE hips (lower y)
    })
    assert is_squat(yes) is True
    no = make_pose({
        LEFT_HIP: (0.4, 0.5), RIGHT_HIP: (0.6, 0.5),
        LEFT_KNEE: (0.4, 0.7), RIGHT_KNEE: (0.6, 0.7),  # knees BELOW hips (standing)
    })
    assert is_squat(no) is False


def test_target_poses_registry_has_six():
    assert len(TARGET_POSES) == 6


# ---- Game state machine tests ----

def _config_for_test() -> PoseSimonConfig:
    return PoseSimonConfig(
        starting_sequence_length=1,
        demo_pose_ms=100,
        demo_gap_ms=50,
        hold_ms=100,
        timeout_per_pose_ms=500,
        resolve_hold_ms=100,
    )


def arms_up_pose() -> Pose:
    return make_pose({
        NOSE: (0.5, 0.4),
        LEFT_SHOULDER: (0.4, 0.3), RIGHT_SHOULDER: (0.6, 0.3),
        LEFT_HIP: (0.4, 0.7), RIGHT_HIP: (0.6, 0.7),
        LEFT_WRIST: (0.4, 0.1), RIGHT_WRIST: (0.6, 0.1),
    })


def neutral_pose() -> Pose:
    return make_pose({
        NOSE: (0.5, 0.4),
        LEFT_SHOULDER: (0.4, 0.3), RIGHT_SHOULDER: (0.6, 0.3),
        LEFT_HIP: (0.4, 0.7), RIGHT_HIP: (0.6, 0.7),
        LEFT_WRIST: (0.4, 0.7), RIGHT_WRIST: (0.6, 0.7),
    })


def test_starts_in_demo_phase():
    g = PoseSimonGame(now_ms=0, config=_config_for_test(), seed=1)
    g.tick(0, None, None)
    s = g.to_dict()
    assert s["phase"] == "demo"
    assert s["round"] == 1
    assert len(s["sequence"]) == 1


def test_advances_to_input_after_demo():
    cfg = _config_for_test()
    g = PoseSimonGame(now_ms=0, config=cfg, seed=1)
    # Demo runs for sequence_length * (demo_pose_ms + demo_gap_ms) = 1 * (100 + 50) = 150
    g.tick(0, None, None)
    g.tick(50, None, None)
    g.tick(160, None, None)
    s = g.to_dict()
    assert s["phase"] == "input"


def test_player_completes_short_sequence():
    cfg = _config_for_test()
    g = PoseSimonGame(now_ms=0, config=cfg, seed=1)
    # Force the sequence to a known pose so the test pose actually matches
    g._sequence = ["arms_up"]  # type: ignore[attr-defined]
    # Drive through demo
    g.tick(0, None, None)
    g.tick(160, None, None)  # past demo, now in INPUT
    assert g.to_dict()["phase"] == "input"
    p1 = arms_up_pose()
    p2 = arms_up_pose()
    # Hold for hold_ms (100ms) + a buffer
    g.tick(170, p1, p2)
    g.tick(280, p1, p2)  # 280 - 170 = 110 ms held
    s = g.to_dict()
    # Both completed → resolve, then next round
    g.tick(285, p1, p2)
    s = g.to_dict()
    assert s["phase"] in ("resolve", "demo", "input")  # implementation may resolve quickly
    # Wait for resolve to finish, next round should start
    g.tick(500, neutral_pose(), neutral_pose())
    s = g.to_dict()
    assert s["round"] == 2 or s["phase"] == "resolve"


def test_game_ends_when_one_completes_other_does_not():
    cfg = _config_for_test()
    g = PoseSimonGame(now_ms=0, config=cfg, seed=1)
    g._sequence = ["arms_up"]  # type: ignore[attr-defined]
    g.tick(0, None, None)
    g.tick(160, None, None)
    # Only P1 holds the right pose; P2 stays neutral
    p1 = arms_up_pose()
    p2 = neutral_pose()
    # Hold P1 long enough to complete; let timeout pass for P2
    g.tick(170, p1, p2)
    g.tick(290, p1, p2)  # 120 ms — past hold
    # Wait past the round timeout (500ms from input start at ~160ms = 660)
    g.tick(700, neutral_pose(), neutral_pose())
    g.tick(900, neutral_pose(), neutral_pose())
    assert g.is_done() is True
    assert g.winner() == 1


def test_game_ends_in_draw_when_both_fail_at_same_index():
    cfg = _config_for_test()
    g = PoseSimonGame(now_ms=0, config=cfg, seed=1)
    g._sequence = ["arms_up"]  # type: ignore[attr-defined]
    g.tick(0, None, None)
    g.tick(160, None, None)
    # Neither player matches the pose
    g.tick(200, neutral_pose(), neutral_pose())
    g.tick(700, neutral_pose(), neutral_pose())  # past timeout
    g.tick(900, neutral_pose(), neutral_pose())  # past resolve
    assert g.is_done() is True
    assert g.winner() is None


def test_summary_shape():
    cfg = _config_for_test()
    g = PoseSimonGame(now_ms=0, config=cfg, seed=1)
    g._sequence = ["arms_up"]  # type: ignore[attr-defined]
    g.tick(0, None, None)
    g.tick(160, None, None)
    g.tick(700, neutral_pose(), neutral_pose())  # past timeout — both fail
    g.tick(900, neutral_pose(), neutral_pose())
    s = g.summary()
    assert s["name"] == "Pose Simon"
    assert s["metric_unit"] == "rounds cleared"
    assert s["winner"] is None
    assert "p1_metric" in s and "p2_metric" in s
