"""Pose Simon. See spec §7.3.

Each round shows a growing sequence of target poses, then both players try
to reproduce it from memory. A pose counts as "matched" when held continuously
for `hold_ms`. Round timeout is `timeout_per_pose_ms × sequence_length`.

Game outcome:
- Both complete → continue to next round (sequence grows by 1).
- One completes, the other doesn't → the one who completed wins.
- Neither completes → whoever has more correctly-held poses wins; ties → draw.
"""
import random
from dataclasses import dataclass
from typing import Optional
from backend.config import PoseSimonConfig
from backend.games.base import Game
from backend.pose.types import (
    Pose, NOSE, LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP,
    LEFT_KNEE, RIGHT_KNEE, LEFT_WRIST, RIGHT_WRIST,
)


# Target pose names (registry).
TARGET_POSES: tuple[str, ...] = (
    "arms_up", "t_pose", "left_arm_up", "right_arm_up", "hands_on_hips", "squat",
)


# ---- Pose detectors ----

def _kp_ok(pose: Pose, idx: int, conf_threshold: float = 0.3) -> bool:
    return bool(pose.keypoints[idx, 2] >= conf_threshold)


def is_arms_up(pose: Pose) -> bool:
    if not all(_kp_ok(pose, i) for i in (NOSE, LEFT_WRIST, RIGHT_WRIST)):
        return False
    nose_y = pose.keypoints[NOSE, 1]
    return bool(
        pose.keypoints[LEFT_WRIST, 1] < nose_y
        and pose.keypoints[RIGHT_WRIST, 1] < nose_y
    )


def is_t_pose(pose: Pose, cfg: PoseSimonConfig) -> bool:
    needed = (LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_WRIST, RIGHT_WRIST)
    if not all(_kp_ok(pose, i) for i in needed):
        return False
    ls_x = pose.keypoints[LEFT_SHOULDER, 0]
    rs_x = pose.keypoints[RIGHT_SHOULDER, 0]
    shoulder_width = abs(ls_x - rs_x)
    if shoulder_width <= 0:
        return False
    avg_shoulder_y = 0.5 * (pose.keypoints[LEFT_SHOULDER, 1] + pose.keypoints[RIGHT_SHOULDER, 1])
    lw_x, lw_y = pose.keypoints[LEFT_WRIST, 0], pose.keypoints[LEFT_WRIST, 1]
    rw_x, rw_y = pose.keypoints[RIGHT_WRIST, 0], pose.keypoints[RIGHT_WRIST, 1]
    if abs(lw_y - avg_shoulder_y) > cfg.tpose_y_tolerance:
        return False
    if abs(rw_y - avg_shoulder_y) > cfg.tpose_y_tolerance:
        return False
    if abs(lw_x - ls_x) < cfg.tpose_x_factor * shoulder_width:
        return False
    if abs(rw_x - rs_x) < cfg.tpose_x_factor * shoulder_width:
        return False
    return True


def is_left_arm_up(pose: Pose) -> bool:
    needed = (NOSE, LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_WRIST, RIGHT_WRIST)
    if not all(_kp_ok(pose, i) for i in needed):
        return False
    nose_y = pose.keypoints[NOSE, 1]
    rs_y = pose.keypoints[RIGHT_SHOULDER, 1]
    return bool(
        pose.keypoints[LEFT_WRIST, 1] < nose_y
        and pose.keypoints[RIGHT_WRIST, 1] > rs_y
    )


def is_right_arm_up(pose: Pose) -> bool:
    needed = (NOSE, LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_WRIST, RIGHT_WRIST)
    if not all(_kp_ok(pose, i) for i in needed):
        return False
    nose_y = pose.keypoints[NOSE, 1]
    ls_y = pose.keypoints[LEFT_SHOULDER, 1]
    return bool(
        pose.keypoints[RIGHT_WRIST, 1] < nose_y
        and pose.keypoints[LEFT_WRIST, 1] > ls_y
    )


def is_hands_on_hips(pose: Pose, cfg: PoseSimonConfig) -> bool:
    needed = (LEFT_HIP, RIGHT_HIP, LEFT_WRIST, RIGHT_WRIST)
    if not all(_kp_ok(pose, i) for i in needed):
        return False
    lh = pose.keypoints[LEFT_HIP]
    rh = pose.keypoints[RIGHT_HIP]
    lw = pose.keypoints[LEFT_WRIST]
    rw = pose.keypoints[RIGHT_WRIST]
    d_left = ((lw[0] - lh[0]) ** 2 + (lw[1] - lh[1]) ** 2) ** 0.5
    d_right = ((rw[0] - rh[0]) ** 2 + (rw[1] - rh[1]) ** 2) ** 0.5
    return bool(d_left <= cfg.hip_radius and d_right <= cfg.hip_radius)


def is_squat(pose: Pose) -> bool:
    needed = (LEFT_HIP, RIGHT_HIP, LEFT_KNEE, RIGHT_KNEE)
    if not all(_kp_ok(pose, i) for i in needed):
        return False
    avg_hip_y = 0.5 * (pose.keypoints[LEFT_HIP, 1] + pose.keypoints[RIGHT_HIP, 1])
    avg_knee_y = 0.5 * (pose.keypoints[LEFT_KNEE, 1] + pose.keypoints[RIGHT_KNEE, 1])
    # Squatting: hips drop close to knees. With image y top-to-bottom, "drop"
    # means hip.y becomes LARGER. The strict spec is hip.y > knee.y; that's
    # an extreme squat. In practice anyone bending well below standing has
    # hip.y approaching knee.y, so use hip.y >= knee.y - a small slack.
    # Using strict per spec for v1.
    return bool(avg_hip_y > avg_knee_y)


_DETECTORS = {
    "arms_up": lambda pose, cfg: is_arms_up(pose),
    "t_pose": lambda pose, cfg: is_t_pose(pose, cfg),
    "left_arm_up": lambda pose, cfg: is_left_arm_up(pose),
    "right_arm_up": lambda pose, cfg: is_right_arm_up(pose),
    "hands_on_hips": lambda pose, cfg: is_hands_on_hips(pose, cfg),
    "squat": lambda pose, cfg: is_squat(pose),
}


def matches_pose(pose: Optional[Pose], target: str, cfg: PoseSimonConfig) -> bool:
    if pose is None:
        return False
    fn = _DETECTORS.get(target)
    if fn is None:
        return False
    return fn(pose, cfg)


# ---- Per-player input tracker ----

@dataclass
class _PlayerProgress:
    index: int = 0  # next pose to match
    holding_since_ms: Optional[int] = None  # when current target started being matched
    completed: bool = False


# ---- Game ----

class PoseSimonGame(Game):
    PHASE_DEMO = "demo"
    PHASE_INPUT = "input"
    PHASE_RESOLVE = "resolve"
    PHASE_DONE = "done"

    def __init__(self, now_ms: int, config: PoseSimonConfig, seed: int = 0):
        self._cfg = config
        self._rng = random.Random(seed)
        self._round = 1
        self._phase = self.PHASE_DEMO
        self._phase_started_ms = now_ms
        self._sequence: list[str] = self._build_sequence(config.starting_sequence_length)
        self._p1 = _PlayerProgress()
        self._p2 = _PlayerProgress()
        self._rounds_cleared_p1 = 0
        self._rounds_cleared_p2 = 0
        self._final_winner: Optional[int] = None  # set when game ends

    def _build_sequence(self, length: int) -> list[str]:
        # Each round picks a fresh sequence; growing the sequence means a
        # longer fresh sequence (not the previous + one), which is simpler.
        return [self._rng.choice(TARGET_POSES) for _ in range(length)]

    def _demo_total_ms(self) -> int:
        per_pose = self._cfg.demo_pose_ms + self._cfg.demo_gap_ms
        return per_pose * len(self._sequence)

    def _input_timeout_ms(self) -> int:
        return self._cfg.timeout_per_pose_ms * len(self._sequence)

    def tick(self, now_ms: int, p1: Optional[Pose], p2: Optional[Pose]) -> None:
        if self._phase == self.PHASE_DONE:
            return

        if self._phase == self.PHASE_DEMO:
            if now_ms - self._phase_started_ms >= self._demo_total_ms():
                self._phase = self.PHASE_INPUT
                self._phase_started_ms = now_ms
            return

        if self._phase == self.PHASE_INPUT:
            self._tick_player(p1, self._p1, now_ms)
            self._tick_player(p2, self._p2, now_ms)
            elapsed = now_ms - self._phase_started_ms
            if (self._p1.completed and self._p2.completed) or elapsed >= self._input_timeout_ms():
                self._enter_resolve(now_ms)
            return

        if self._phase == self.PHASE_RESOLVE:
            if now_ms - self._phase_started_ms >= self._cfg.resolve_hold_ms:
                self._after_resolve(now_ms)

    def _tick_player(self, pose: Optional[Pose], state: _PlayerProgress, now_ms: int) -> None:
        if state.completed:
            return
        if state.index >= len(self._sequence):
            state.completed = True
            return
        target = self._sequence[state.index]
        if matches_pose(pose, target, self._cfg):
            if state.holding_since_ms is None:
                state.holding_since_ms = now_ms
            elif now_ms - state.holding_since_ms >= self._cfg.hold_ms:
                state.index += 1
                state.holding_since_ms = None
                if state.index >= len(self._sequence):
                    state.completed = True
        else:
            state.holding_since_ms = None

    def _enter_resolve(self, now_ms: int) -> None:
        self._phase = self.PHASE_RESOLVE
        self._phase_started_ms = now_ms
        if self._p1.completed:
            self._rounds_cleared_p1 += 1
        if self._p2.completed:
            self._rounds_cleared_p2 += 1

    def _after_resolve(self, now_ms: int) -> None:
        if self._p1.completed and self._p2.completed:
            # Both succeeded — grow sequence and continue
            self._round += 1
            self._sequence = self._build_sequence(len(self._sequence) + 1)
            self._p1 = _PlayerProgress()
            self._p2 = _PlayerProgress()
            self._phase = self.PHASE_DEMO
            self._phase_started_ms = now_ms
            return

        # Game ends
        self._phase = self.PHASE_DONE
        if self._p1.completed and not self._p2.completed:
            self._final_winner = 1
        elif self._p2.completed and not self._p1.completed:
            self._final_winner = 2
        else:
            # Neither completed — compare progress index
            if self._p1.index > self._p2.index:
                self._final_winner = 1
            elif self._p2.index > self._p1.index:
                self._final_winner = 2
            else:
                self._final_winner = None

    def is_done(self) -> bool:
        return self._phase == self.PHASE_DONE

    def winner(self) -> Optional[int]:
        return self._final_winner if self.is_done() else None

    def to_dict(self) -> dict:
        return {
            "type": "pose_simon",
            "round": self._round,
            "phase": self._phase,
            "sequence": list(self._sequence),
            "p1_index": self._p1.index,
            "p2_index": self._p2.index,
            "p1_completed": self._p1.completed,
            "p2_completed": self._p2.completed,
            "rounds_cleared_p1": self._rounds_cleared_p1,
            "rounds_cleared_p2": self._rounds_cleared_p2,
        }

    def summary(self) -> dict:
        return {
            "name": "Pose Simon",
            "p1_metric": self._rounds_cleared_p1,
            "p2_metric": self._rounds_cleared_p2,
            "metric_unit": "rounds cleared",
            "winner": self.winner(),
        }
