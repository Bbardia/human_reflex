"""Touch the Circle game. See spec §7.1.

Coordinate system note: keypoints are in full-frame normalized coords (0..1).
The target position is in HALF-FRAME coords (0..1 within each player's half),
so Player 1's wrist-in-circle test maps target.x to full-frame x via
  full_x = target.x * 0.5
and for Player 2:
  full_x = 0.5 + target.x * 0.5

The target appears at the SAME (x,y) in both halves so it's pure reaction parity.
"""
import math
import random
from dataclasses import dataclass, field
from typing import Optional
from backend.config import TouchCircleConfig
from backend.games.base import Game
from backend.pose.types import Pose, LEFT_WRIST, RIGHT_WRIST


@dataclass
class _RoundResult:
    p1_time_ms: Optional[int] = None
    p2_time_ms: Optional[int] = None
    p1_false_start: bool = False
    p2_false_start: bool = False

    def settled(self) -> bool:
        return self.p1_time_ms is not None and self.p2_time_ms is not None


@dataclass
class _WristTrack:
    """Tracks recent wrist positions per player to detect fast preroll motion."""
    last_x: Optional[float] = None
    last_y: Optional[float] = None
    last_ts: Optional[int] = None
    fast_motion_started_ms: Optional[int] = None

    def update(self, x: float, y: float, ts: int, threshold_per_sec: float) -> bool:
        """Returns True if sustained fast motion has occurred for >100ms.
        Caller decides what "100 ms" means via the gate."""
        moving_fast = False
        if self.last_x is not None and self.last_ts is not None and ts > self.last_ts:
            dt = (ts - self.last_ts) / 1000.0
            dx = abs(x - self.last_x)
            dy = abs(y - self.last_y) if self.last_y is not None else 0
            speed = math.hypot(dx, dy) / max(dt, 1e-6)
            moving_fast = speed > threshold_per_sec
        if moving_fast:
            if self.fast_motion_started_ms is None:
                self.fast_motion_started_ms = ts
        else:
            self.fast_motion_started_ms = None
        self.last_x = x
        self.last_y = y
        self.last_ts = ts
        return self.fast_motion_started_ms is not None

    def fast_motion_duration_ms(self, now_ms: int) -> int:
        if self.fast_motion_started_ms is None:
            return 0
        return now_ms - self.fast_motion_started_ms

    def reset(self) -> None:
        self.fast_motion_started_ms = None


class TouchCircleGame(Game):
    PHASE_PREROLL = "preroll"
    PHASE_ACTIVE = "active"
    PHASE_DONE = "done"

    def __init__(self, now_ms: int, config: TouchCircleConfig, seed: int = 0):
        self._cfg = config
        self._rng = random.Random(seed)
        self._round = 1
        self._phase = self.PHASE_PREROLL
        self._round_started_ms = now_ms
        self._target_appears_at_ms = now_ms + self._rand_preroll()
        self._target: Optional[tuple[float, float, float]] = None  # (x, y, radius) in half-screen coords
        self._target_appeared_ms: Optional[int] = None
        self._results: list[_RoundResult] = [_RoundResult()]
        self._track_p1 = _WristTrack()
        self._track_p2 = _WristTrack()

    # ---- helpers ----

    def _rand_preroll(self) -> int:
        return self._rng.randint(self._cfg.preroll_ms_min, self._cfg.preroll_ms_max)

    def _spawn_target(self) -> tuple[float, float, float]:
        # Keep target away from edges so wrists can reach it
        radius = self._cfg.target_size_pct
        margin = radius + 0.05
        x = self._rng.uniform(margin, 1.0 - margin)
        y = self._rng.uniform(margin, 1.0 - margin)
        return x, y, radius

    @staticmethod
    def _wrist_xy(pose: Optional[Pose]) -> Optional[tuple[float, float]]:
        """Return whichever wrist is more confident, in full-frame coords."""
        if pose is None:
            return None
        lx, ly, lc = pose.kp(LEFT_WRIST)
        rx, ry, rc = pose.kp(RIGHT_WRIST)
        if max(lc, rc) < 0.3:
            return None
        return (lx, ly) if lc >= rc else (rx, ry)

    def _hit_test(self, wrist_full: Optional[tuple[float, float]], player_idx: int) -> bool:
        if wrist_full is None or self._target is None:
            return False
        wx, wy = wrist_full
        tx, ty, tr = self._target
        # Map full-frame wrist to half-frame x for hit test
        if player_idx == 1:
            half_x = wx * 2.0  # left half: 0..0.5 → 0..1
        else:
            half_x = (wx - 0.5) * 2.0  # right half: 0.5..1 → 0..1
        if half_x < 0.0 or half_x > 1.0:
            return False
        return math.hypot(half_x - tx, wy - ty) <= tr

    # ---- main tick ----

    def tick(self, now_ms: int, p1: Optional[Pose], p2: Optional[Pose]) -> None:
        if self._phase == self.PHASE_DONE:
            return

        if self._phase == self.PHASE_PREROLL:
            self._update_false_start_tracking(now_ms, p1, p2)
            if now_ms >= self._target_appears_at_ms:
                self._target = self._spawn_target()
                self._target_appeared_ms = now_ms
                self._phase = self.PHASE_ACTIVE
            return

        # ACTIVE phase
        result = self._results[-1]
        assert self._target_appeared_ms is not None

        if not result.p1_false_start and result.p1_time_ms is None:
            if self._hit_test(self._wrist_xy(p1), 1):
                result.p1_time_ms = now_ms - self._target_appeared_ms
        if not result.p2_false_start and result.p2_time_ms is None:
            if self._hit_test(self._wrist_xy(p2), 2):
                result.p2_time_ms = now_ms - self._target_appeared_ms

        if result.settled():
            self._advance_round(now_ms)

    def _update_false_start_tracking(
        self, now_ms: int, p1: Optional[Pose], p2: Optional[Pose]
    ) -> None:
        result = self._results[-1]
        thresh = self._cfg.false_start_speed_threshold
        min_dur = self._cfg.false_start_min_duration_ms
        penalty = self._cfg.false_start_penalty_ms

        for player_idx, pose, track, key_time, key_flag in [
            (1, p1, self._track_p1, "p1_time_ms", "p1_false_start"),
            (2, p2, self._track_p2, "p2_time_ms", "p2_false_start"),
        ]:
            wrist = self._wrist_xy(pose)
            if wrist is None:
                continue
            if getattr(result, key_flag):
                continue
            # Check duration BEFORE updating: if fast motion was already sustained
            # past the threshold *as of now_ms*, fire the penalty regardless of
            # this tick's instantaneous speed. (A single slow-frame should not
            # erase a clearly false-started motion.)
            if track.fast_motion_duration_ms(now_ms) >= min_dur:
                setattr(result, key_flag, True)
                setattr(result, key_time, penalty)
                track.reset()
                track.update(wrist[0], wrist[1], now_ms, thresh)
                continue
            track.update(wrist[0], wrist[1], now_ms, thresh)
            if track.fast_motion_duration_ms(now_ms) >= min_dur:
                setattr(result, key_flag, True)
                setattr(result, key_time, penalty)
                track.reset()

    def _advance_round(self, now_ms: int) -> None:
        if self._round >= self._cfg.rounds:
            self._phase = self.PHASE_DONE
            self._target = None
            return
        self._round += 1
        self._phase = self.PHASE_PREROLL
        self._target = None
        self._target_appeared_ms = None
        self._round_started_ms = now_ms
        self._target_appears_at_ms = now_ms + self._rand_preroll()
        self._results.append(_RoundResult())
        self._track_p1.reset()
        self._track_p2.reset()

    # ---- Game interface ----

    def is_done(self) -> bool:
        return self._phase == self.PHASE_DONE

    def winner(self) -> Optional[int]:
        if not self.is_done():
            return None
        p1_avg = self._mean_time(player=1)
        p2_avg = self._mean_time(player=2)
        if p1_avg < p2_avg:
            return 1
        if p2_avg < p1_avg:
            return 2
        return None

    def _mean_time(self, player: int) -> float:
        key = "p1_time_ms" if player == 1 else "p2_time_ms"
        times = [getattr(r, key) for r in self._results if getattr(r, key) is not None]
        if not times:
            return float("inf")
        return sum(times) / len(times)

    def to_dict(self) -> dict:
        return {
            "type": "touch_circle",
            "round": self._round,
            "total_rounds": self._cfg.rounds,
            "phase": self._phase,
            "target": (
                {"x": self._target[0], "y": self._target[1], "radius": self._target[2]}
                if self._target else None
            ),
            "results": [
                {
                    "p1_time_ms": r.p1_time_ms,
                    "p2_time_ms": r.p2_time_ms,
                    "p1_false_start": r.p1_false_start,
                    "p2_false_start": r.p2_false_start,
                }
                for r in self._results
            ],
        }

    def summary(self) -> dict:
        p1_avg = self._mean_time(1)
        p2_avg = self._mean_time(2)
        return {
            "name": "Touch the Circle",
            "p1_metric": round(p1_avg) if p1_avg != float("inf") else None,
            "p2_metric": round(p2_avg) if p2_avg != float("inf") else None,
            "metric_unit": "ms (avg reaction)",
            "winner": self.winner(),
        }
