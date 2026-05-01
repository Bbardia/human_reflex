"""Goalie game. See spec §7.2.

Each shot: random pre-roll, then a "ball" spawns and travels for
ball_travel_ms toward one of 5 zones in the half-screen. A "save" is
recorded the first time any of the player's wrist/ankle/head keypoints
enter the zone, even before the ball arrives. After ball travel completes
we hold the resolved state for resolve_hold_ms before advancing.

Coordinate system note: keypoints are in full-frame normalized coords (0..1).
Zone bounds are in HALF-FRAME coords (0..1 within each player's half), so we
map a wrist at full-frame x=full_x to half_x via:
  P1: half_x = full_x * 2.0     (since P1 lives in 0..0.5)
  P2: half_x = (full_x - 0.5) * 2.0   (since P2 lives in 0.5..1.0)
The ball appears at the SAME zone for both halves so it's pure parity.
"""
import random
from dataclasses import dataclass
from typing import Optional
from backend.config import GoalieConfig
from backend.games.base import Game
from backend.pose.types import (
    Pose, LEFT_WRIST, RIGHT_WRIST, LEFT_ANKLE, RIGHT_ANKLE, NOSE,
)


SAVE_KEYPOINTS = (LEFT_WRIST, RIGHT_WRIST, LEFT_ANKLE, RIGHT_ANKLE, NOSE)


@dataclass
class _ShotResult:
    zone: int
    p1_saved: bool = False
    p2_saved: bool = False
    p1_save_time_ms: Optional[int] = None
    p2_save_time_ms: Optional[int] = None


class GoalieGame(Game):
    PHASE_PREROLL = "preroll"
    PHASE_ACTIVE = "active"
    PHASE_DONE = "done"

    def __init__(self, now_ms: int, config: GoalieConfig, seed: int = 0):
        self._cfg = config
        self._rng = random.Random(seed)
        self._shot = 1
        self._phase = self.PHASE_PREROLL
        self._ball_spawn_at_ms = now_ms + self._rand_preroll()
        self._ball_spawned_at_ms: Optional[int] = None
        self._ball_zone: Optional[int] = None
        self._results: list[_ShotResult] = []

    def _rand_preroll(self) -> int:
        return self._rng.randint(self._cfg.preroll_ms_min, self._cfg.preroll_ms_max)

    def _spawn_ball(self, now_ms: int) -> None:
        zone_idx = self._rng.randint(0, len(self._cfg.zones) - 1)
        self._ball_zone = zone_idx
        self._ball_spawned_at_ms = now_ms
        self._results.append(_ShotResult(zone=zone_idx))

    def _resolve_at_ms(self) -> int:
        assert self._ball_spawned_at_ms is not None
        return self._ball_spawned_at_ms + self._cfg.ball_travel_ms + self._cfg.resolve_hold_ms

    def _check_save(self, pose: Optional[Pose], player_idx: int, zone_idx: int) -> bool:
        if pose is None:
            return False
        zmin_x, zmin_y, zmax_x, zmax_y = self._cfg.zones[zone_idx]
        for kp in SAVE_KEYPOINTS:
            x, y, conf = pose.kp(kp)
            if conf < 0.3:
                continue
            if player_idx == 1:
                half_x = x * 2.0
            else:
                half_x = (x - 0.5) * 2.0
            if half_x < 0.0 or half_x > 1.0:
                continue
            if zmin_x <= half_x <= zmax_x and zmin_y <= y <= zmax_y:
                return True
        return False

    def tick(self, now_ms: int, p1: Optional[Pose], p2: Optional[Pose]) -> None:
        if self._phase == self.PHASE_DONE:
            return

        if self._phase == self.PHASE_PREROLL:
            if now_ms >= self._ball_spawn_at_ms:
                self._spawn_ball(now_ms)
                self._phase = self.PHASE_ACTIVE
            return

        # ACTIVE
        assert self._ball_spawned_at_ms is not None
        assert self._ball_zone is not None
        result = self._results[-1]

        if not result.p1_saved and self._check_save(p1, 1, self._ball_zone):
            result.p1_saved = True
            result.p1_save_time_ms = now_ms - self._ball_spawned_at_ms
        if not result.p2_saved and self._check_save(p2, 2, self._ball_zone):
            result.p2_saved = True
            result.p2_save_time_ms = now_ms - self._ball_spawned_at_ms

        if now_ms >= self._resolve_at_ms():
            self._advance_shot(now_ms)

    def _advance_shot(self, now_ms: int) -> None:
        if self._shot >= self._cfg.shots:
            self._phase = self.PHASE_DONE
            self._ball_zone = None
            self._ball_spawned_at_ms = None
            return
        self._shot += 1
        self._phase = self.PHASE_PREROLL
        self._ball_zone = None
        self._ball_spawned_at_ms = None
        self._ball_spawn_at_ms = now_ms + self._rand_preroll()

    def is_done(self) -> bool:
        return self._phase == self.PHASE_DONE

    def winner(self) -> Optional[int]:
        if not self.is_done():
            return None
        p1_saves = sum(1 for r in self._results if r.p1_saved)
        p2_saves = sum(1 for r in self._results if r.p2_saved)
        if p1_saves > p2_saves:
            return 1
        if p2_saves > p1_saves:
            return 2
        # Tiebreak: lowest mean save time
        p1_times = [r.p1_save_time_ms for r in self._results if r.p1_save_time_ms is not None]
        p2_times = [r.p2_save_time_ms for r in self._results if r.p2_save_time_ms is not None]
        p1_avg = sum(p1_times) / len(p1_times) if p1_times else float("inf")
        p2_avg = sum(p2_times) / len(p2_times) if p2_times else float("inf")
        if p1_avg < p2_avg:
            return 1
        if p2_avg < p1_avg:
            return 2
        return None

    def to_dict(self) -> dict:
        ball: Optional[dict] = None
        if self._ball_zone is not None and self._ball_spawned_at_ms is not None:
            ball = {
                "zone": self._ball_zone,
                "spawned_at_ms": self._ball_spawned_at_ms,
                "travel_ms": self._cfg.ball_travel_ms,
            }
        return {
            "type": "goalie",
            "shot": self._shot,
            "total_shots": self._cfg.shots,
            "phase": self._phase,
            "ball": ball,
            "zones": [list(z) for z in self._cfg.zones],
            "results": [
                {
                    "zone": r.zone,
                    "p1_saved": r.p1_saved,
                    "p2_saved": r.p2_saved,
                    "p1_save_time_ms": r.p1_save_time_ms,
                    "p2_save_time_ms": r.p2_save_time_ms,
                }
                for r in self._results
            ],
        }

    def summary(self) -> dict:
        p1_saves = sum(1 for r in self._results if r.p1_saved)
        p2_saves = sum(1 for r in self._results if r.p2_saved)
        return {
            "name": "Goalie",
            "p1_metric": p1_saves,
            "p2_metric": p2_saves,
            "metric_unit": "saves",
            "winner": self.winner(),
        }
