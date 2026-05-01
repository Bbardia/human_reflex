"""Laser Limbo. See spec §7.4.

A 30-second arena where lasers sweep across each player's half. Same laser
pattern is rendered to both halves so it's a fair contest. Player loses 1 HP
per laser collision (with a 500 ms invulnerability window). Game winner is
last alive; ties broken by HP, then by fewer total hits.

Coordinate system note: keypoints are in full-frame normalized coords (0..1).
For horizontal lasers, the laser's y-position applies directly to keypoint y.
For vertical lasers, the laser's x-position is in HALF-frame coords (0..1
within each player's half), so we map full-frame x via:
  P1: half_x = full_x * 2.0
  P2: half_x = (full_x - 0.5) * 2.0
The laser is "active" against a player's keypoint only if the keypoint's
half_x falls in [0, 1].
"""
import random
from dataclasses import dataclass, field
from typing import Optional
from backend.config import LaserLimboConfig
from backend.games.base import Game
from backend.pose.types import Pose, NUM_KEYPOINTS


@dataclass
class _Laser:
    spawn_ms: int
    duration_ms: int
    orientation: str  # 'h' for horizontal sweep (vertical motion), 'v' for vertical sweep (horizontal motion)
    direction: int   # +1 or -1
    thickness: float

    def position(self, now_ms: int) -> Optional[float]:
        """Returns the laser's center coord at now_ms, or None if outside its lifetime.
        For horizontal: a y-coord that linearly travels from -thickness to 1+thickness
        (or reverse). For vertical: same on x-axis."""
        if now_ms < self.spawn_ms or now_ms > self.spawn_ms + self.duration_ms:
            return None
        t = (now_ms - self.spawn_ms) / self.duration_ms  # 0..1
        span = 1.0 + 2.0 * self.thickness  # full sweep distance from -thickness to 1+thickness
        if self.direction == +1:
            return -self.thickness + t * span
        else:
            return 1.0 + self.thickness - t * span

    def hits(self, pose: Pose, player_idx: int, now_ms: int) -> bool:
        pos = self.position(now_ms)
        if pos is None:
            return False
        for kp in range(NUM_KEYPOINTS):
            x = float(pose.keypoints[kp, 0])
            y = float(pose.keypoints[kp, 1])
            c = float(pose.keypoints[kp, 2])
            if c < 0.3:
                continue
            if self.orientation == "h":
                if abs(y - pos) <= self.thickness:
                    return True
            else:  # vertical
                if player_idx == 1:
                    half_x = x * 2.0
                else:
                    half_x = (x - 0.5) * 2.0
                if 0.0 <= half_x <= 1.0 and abs(half_x - pos) <= self.thickness:
                    return True
        return False


class LaserLimboGame(Game):
    PHASE_ACTIVE = "active"
    PHASE_RESOLVE = "resolve"
    PHASE_DONE = "done"

    def __init__(self, now_ms: int, config: LaserLimboConfig, seed: int = 0):
        self._cfg = config
        self._rng = random.Random(seed)
        self._phase = self.PHASE_ACTIVE
        self._match_started_ms = now_ms
        self._next_spawn_ms: int = now_ms + self._next_interarrival_ms(now_ms)
        self._active_lasers: list[_Laser] = []
        self._p1_hp: int = config.starting_hp
        self._p2_hp: int = config.starting_hp
        self._p1_hits: int = 0
        self._p2_hits: int = 0
        self._p1_invuln_until: int = 0
        self._p2_invuln_until: int = 0
        self._resolve_started_ms: Optional[int] = None
        self._final_winner: Optional[int] = None

    def _current_rate(self, now_ms: int) -> float:
        elapsed_s = (now_ms - self._match_started_ms) / 1000.0
        if elapsed_s < self._cfg.ramp_at_s:
            return self._cfg.rate_hz_early
        return self._cfg.rate_hz_late

    def _next_interarrival_ms(self, now_ms: int) -> int:
        rate = self._current_rate(now_ms)
        if rate <= 0:
            return 1_000_000
        # exponential interarrival (Poisson process) — guard against extreme values
        secs = self._rng.expovariate(rate)
        return max(1, int(secs * 1000))

    def _spawn_laser(self, now_ms: int) -> None:
        elapsed_s = (now_ms - self._match_started_ms) / 1000.0
        # Vertical lasers only after the ramp
        orientations = ("h", "v") if elapsed_s >= self._cfg.ramp_at_s else ("h",)
        orientation = self._rng.choice(orientations)
        direction = self._rng.choice((+1, -1))
        self._active_lasers.append(_Laser(
            spawn_ms=now_ms,
            duration_ms=self._cfg.laser_duration_ms,
            orientation=orientation,
            direction=direction,
            thickness=self._cfg.laser_thickness,
        ))

    def _prune_expired(self, now_ms: int) -> None:
        self._active_lasers = [
            laser for laser in self._active_lasers
            if now_ms <= laser.spawn_ms + laser.duration_ms
        ]

    def _check_collisions(
        self, now_ms: int, p1: Optional[Pose], p2: Optional[Pose]
    ) -> None:
        for laser in self._active_lasers:
            if p1 is not None and self._p1_hp > 0 and now_ms >= self._p1_invuln_until:
                if laser.hits(p1, player_idx=1, now_ms=now_ms):
                    self._p1_hp = max(0, self._p1_hp - 1)
                    self._p1_hits += 1
                    self._p1_invuln_until = now_ms + self._cfg.invuln_ms
            if p2 is not None and self._p2_hp > 0 and now_ms >= self._p2_invuln_until:
                if laser.hits(p2, player_idx=2, now_ms=now_ms):
                    self._p2_hp = max(0, self._p2_hp - 1)
                    self._p2_hits += 1
                    self._p2_invuln_until = now_ms + self._cfg.invuln_ms

    def tick(self, now_ms: int, p1: Optional[Pose], p2: Optional[Pose]) -> None:
        if self._phase == self.PHASE_DONE:
            return

        if self._phase == self.PHASE_ACTIVE:
            # Spawn lasers per Poisson schedule
            while now_ms >= self._next_spawn_ms:
                self._spawn_laser(self._next_spawn_ms)
                self._next_spawn_ms += self._next_interarrival_ms(self._next_spawn_ms)
            self._prune_expired(now_ms)
            self._check_collisions(now_ms, p1, p2)
            elapsed_ms = now_ms - self._match_started_ms
            both_dead = self._p1_hp <= 0 and self._p2_hp <= 0
            if elapsed_ms >= int(self._cfg.match_duration_s * 1000) or both_dead:
                self._phase = self.PHASE_RESOLVE
                self._resolve_started_ms = now_ms
            return

        if self._phase == self.PHASE_RESOLVE:
            assert self._resolve_started_ms is not None
            if now_ms - self._resolve_started_ms >= self._cfg.resolve_hold_ms:
                self._compute_winner()
                self._phase = self.PHASE_DONE

    def _compute_winner(self) -> None:
        if self._p1_hp > self._p2_hp:
            self._final_winner = 1
        elif self._p2_hp > self._p1_hp:
            self._final_winner = 2
        else:
            # tied HP — fewer hits wins
            if self._p1_hits < self._p2_hits:
                self._final_winner = 1
            elif self._p2_hits < self._p1_hits:
                self._final_winner = 2
            else:
                self._final_winner = None

    def is_done(self) -> bool:
        return self._phase == self.PHASE_DONE

    def winner(self) -> Optional[int]:
        return self._final_winner if self.is_done() else None

    def to_dict(self) -> dict:
        return {
            "type": "laser_limbo",
            "phase": self._phase,
            "match_duration_ms": int(self._cfg.match_duration_s * 1000),
            "p1_hp": self._p1_hp,
            "p2_hp": self._p2_hp,
            "p1_hits": self._p1_hits,
            "p2_hits": self._p2_hits,
            "starting_hp": self._cfg.starting_hp,
            "lasers": [
                {
                    "spawn_ms": laser.spawn_ms,
                    "duration_ms": laser.duration_ms,
                    "orientation": laser.orientation,
                    "direction": laser.direction,
                    "thickness": laser.thickness,
                }
                for laser in self._active_lasers
            ],
        }

    def summary(self) -> dict:
        return {
            "name": "Laser Limbo",
            "p1_metric": self._p1_hp,
            "p2_metric": self._p2_hp,
            "metric_unit": "HP",
            "winner": self.winner(),
        }
