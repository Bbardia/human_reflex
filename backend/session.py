"""Top-level session state machine. Plays a fixed sequence of games defined
by GAME_REGISTRY: each game runs to completion, an intermission card shows
the next game, then a 3-2-1 countdown, then the next game. After the last
game the LEADERBOARD shows accumulated results and waits for P1 hands-up
to restart.

P1 controls all menu transitions with the 2-second hands-up gesture.
"""
from dataclasses import replace
from typing import Optional, Callable
from backend.config import CONFIG
from backend.gestures import is_hands_up, GestureHold
from backend.games.base import Game
from backend.games.touch_circle import TouchCircleGame
from backend.games.goalie import GoalieGame
from backend.games.pose_simon import PoseSimonGame
from backend.games.laser_limbo import LaserLimboGame
from backend.pose.types import Pose


SCREEN_TITLE = "title"
SCREEN_COUNTDOWN = "countdown"
SCREEN_GAME = "game"
SCREEN_INTERMISSION = "intermission"
SCREEN_LEADERBOARD = "leaderboard"

COUNTDOWN_MS = 4000
LEADERBOARD_MIN_HOLD_MS = 1500


GameFactory = Callable[[int], Game]


def _touch_circle_factory(now_ms: int) -> Game:
    return TouchCircleGame(now_ms=now_ms, config=CONFIG.touch_circle, seed=now_ms)


def _goalie_factory(now_ms: int) -> Game:
    return GoalieGame(now_ms=now_ms, config=CONFIG.goalie, seed=now_ms)


def _pose_simon_factory(now_ms: int) -> Game:
    return PoseSimonGame(now_ms=now_ms, config=CONFIG.pose_simon, seed=now_ms)


def _laser_limbo_factory(now_ms: int) -> Game:
    return LaserLimboGame(now_ms=now_ms, config=CONFIG.laser_limbo, seed=now_ms)


# Order matters: this is the play sequence.
GAME_REGISTRY: list[GameFactory] = [
    _touch_circle_factory,
    _goalie_factory,
    _pose_simon_factory,
    _laser_limbo_factory,
]


class Session:
    def __init__(self, now_ms: int = 0):
        self._screen = SCREEN_TITLE
        self._screen_entered_ms = now_ms
        self._gesture_hold = GestureHold(hold_ms=CONFIG.gesture.hold_ms)
        self._game: Optional[Game] = None
        self._game_index: int = -1  # -1 before first game starts
        self._completed_summaries: list[dict] = []
        self._countdown_started_ms: Optional[int] = None
        self._intermission_started_ms: Optional[int] = None
        self._sudden_death_active: bool = False

    # ---- transitions ----

    def _enter_title(self, now_ms: int) -> None:
        self._screen = SCREEN_TITLE
        self._screen_entered_ms = now_ms
        self._gesture_hold.reset()
        self._game = None
        self._game_index = -1
        self._completed_summaries = []
        self._countdown_started_ms = None
        self._intermission_started_ms = None
        self._sudden_death_active = False

    def _enter_countdown(self, now_ms: int) -> None:
        self._screen = SCREEN_COUNTDOWN
        self._screen_entered_ms = now_ms
        self._countdown_started_ms = now_ms
        self._gesture_hold.reset()

    def _enter_game(self, now_ms: int) -> None:
        self._screen = SCREEN_GAME
        self._screen_entered_ms = now_ms
        self._game_index += 1
        factory = GAME_REGISTRY[self._game_index]
        self._game = factory(now_ms)

    def _enter_sudden_death_game(self, now_ms: int) -> None:
        """Start a single-round Touch-the-Circle as the tiebreaker."""
        cfg_one_round = replace(CONFIG.touch_circle, rounds=1)
        self._game = TouchCircleGame(now_ms=now_ms, config=cfg_one_round, seed=now_ms)
        self._screen = SCREEN_GAME
        self._screen_entered_ms = now_ms

    def _enter_intermission_no_append(self, now_ms: int) -> None:
        self._screen = SCREEN_INTERMISSION
        self._screen_entered_ms = now_ms
        self._intermission_started_ms = now_ms
        self._gesture_hold.reset()

    def _enter_leaderboard_no_append(self, now_ms: int) -> None:
        self._screen = SCREEN_LEADERBOARD
        self._screen_entered_ms = now_ms
        self._gesture_hold.reset()

    def _enter_intermission(self, now_ms: int, last_summary: dict) -> None:
        self._completed_summaries.append(last_summary)
        self._enter_intermission_no_append(now_ms)

    def _enter_leaderboard(self, now_ms: int, last_summary: dict) -> None:
        self._completed_summaries.append(last_summary)
        self._enter_leaderboard_no_append(now_ms)

    # ---- tick ----

    def tick(self, now_ms: int, p1: Optional[Pose], p2: Optional[Pose]) -> None:
        if self._screen == SCREEN_TITLE:
            self._tick_title(now_ms, p1)
        elif self._screen == SCREEN_COUNTDOWN:
            self._tick_countdown(now_ms)
        elif self._screen == SCREEN_GAME:
            self._tick_game(now_ms, p1, p2)
        elif self._screen == SCREEN_INTERMISSION:
            self._tick_intermission(now_ms, p1)
        elif self._screen == SCREEN_LEADERBOARD:
            self._tick_leaderboard(now_ms, p1)

    def _tick_title(self, now_ms: int, p1: Optional[Pose]) -> None:
        active = p1 is not None and is_hands_up(p1)
        if self._gesture_hold.update(active=active, now_ms=now_ms):
            self._enter_countdown(now_ms)

    def _tick_countdown(self, now_ms: int) -> None:
        started = self._countdown_started_ms if self._countdown_started_ms is not None else now_ms
        if now_ms - started >= COUNTDOWN_MS:
            self._enter_game(now_ms)

    def _tick_game(self, now_ms: int, p1: Optional[Pose], p2: Optional[Pose]) -> None:
        assert self._game is not None
        self._game.tick(now_ms, p1, p2)
        if not self._game.is_done():
            return

        summary = self._game.summary()
        if self._sudden_death_active:
            summary = {**summary, "name": "Sudden Death"}
        self._completed_summaries.append(summary)

        if self._sudden_death_active:
            # Tiebreaker resolved → leaderboard
            self._enter_leaderboard_no_append(now_ms)
            return

        is_last_regular = self._game_index >= len(GAME_REGISTRY) - 1
        if is_last_regular:
            p1_wins = sum(1 for s in self._completed_summaries if s.get("winner") == 1)
            p2_wins = sum(1 for s in self._completed_summaries if s.get("winner") == 2)
            if p1_wins == p2_wins:
                # Tied → sudden-death intermission
                self._sudden_death_active = True
                self._enter_intermission_no_append(now_ms)
                return
            self._enter_leaderboard_no_append(now_ms)
            return

        self._enter_intermission_no_append(now_ms)

    def _tick_intermission(self, now_ms: int, p1: Optional[Pose]) -> None:
        # Auto-advance after intermission_ms; or P1 hands-up advances early
        started = self._intermission_started_ms if self._intermission_started_ms is not None else now_ms
        elapsed = now_ms - started
        if elapsed >= CONFIG.session.intermission_ms:
            if self._sudden_death_active:
                self._enter_sudden_death_game(now_ms)
            else:
                self._enter_countdown(now_ms)
            return
        active = p1 is not None and is_hands_up(p1)
        if self._gesture_hold.update(active=active, now_ms=now_ms):
            if self._sudden_death_active:
                self._enter_sudden_death_game(now_ms)
            else:
                self._enter_countdown(now_ms)

    def _tick_leaderboard(self, now_ms: int, p1: Optional[Pose]) -> None:
        if now_ms - self._screen_entered_ms < LEADERBOARD_MIN_HOLD_MS:
            return
        active = p1 is not None and is_hands_up(p1)
        if self._gesture_hold.update(active=active, now_ms=now_ms):
            self._enter_title(now_ms)

    # ---- serialisation ----

    def to_dict(self, now_ms: int) -> dict:
        out: dict = {
            "screen": self._screen,
            "gesture_progress": self._gesture_hold.progress(now_ms),
        }
        if self._screen == SCREEN_COUNTDOWN and self._countdown_started_ms is not None:
            out["countdown_remaining_ms"] = max(
                0, COUNTDOWN_MS - (now_ms - self._countdown_started_ms)
            )
            out["countdown_ms_total"] = COUNTDOWN_MS
        if self._screen == SCREEN_GAME and self._game is not None:
            out["game"] = self._game.to_dict()
        if self._screen == SCREEN_INTERMISSION:
            last_summary = self._completed_summaries[-1] if self._completed_summaries else None
            started = self._intermission_started_ms if self._intermission_started_ms is not None else now_ms
            elapsed = now_ms - started
            if self._sudden_death_active:
                next_name = "Sudden Death"
                current_index = len(GAME_REGISTRY) + 1
                total_games = len(GAME_REGISTRY) + 1
            else:
                next_idx = self._game_index + 1
                next_name = (
                    _factory_display_name(GAME_REGISTRY[next_idx])
                    if next_idx < len(GAME_REGISTRY) else None
                )
                current_index = next_idx + 1
                total_games = len(GAME_REGISTRY)
            out["intermission"] = {
                "last_summary": last_summary,
                "next_game_name": next_name,
                "current_index": current_index,
                "total_games": total_games,
                "remaining_ms": max(0, CONFIG.session.intermission_ms - elapsed),
                "is_sudden_death": self._sudden_death_active,
            }
        if self._screen == SCREEN_LEADERBOARD:
            out["leaderboard"] = self._build_leaderboard()
        return out

    def snapshot(self, now_ms: int, p1: Optional[Pose], p2: Optional[Pose]) -> dict:
        out = self.to_dict(now_ms)
        out["players"] = {
            "p1": p1.to_dict() if p1 is not None else None,
            "p2": p2.to_dict() if p2 is not None else None,
        }
        return out

    def _build_leaderboard(self) -> dict:
        regular = [s for s in self._completed_summaries if s.get("name") != "Sudden Death"]
        sudden = [s for s in self._completed_summaries if s.get("name") == "Sudden Death"]
        p1_wins = sum(1 for s in regular if s.get("winner") == 1)
        p2_wins = sum(1 for s in regular if s.get("winner") == 2)
        if sudden:
            overall = sudden[0].get("winner")
        elif p1_wins > p2_wins:
            overall = 1
        elif p2_wins > p1_wins:
            overall = 2
        else:
            overall = None
        return {
            "winner": overall,
            "p1_wins": p1_wins,
            "p2_wins": p2_wins,
            "games": self._completed_summaries,
        }


def _factory_display_name(factory: GameFactory) -> str:
    """Best-effort display name for the next game by introspecting the factory."""
    # Each factory closes over a Game class; create a probe instance just to
    # ask the summary's "name" field. We use a fresh instance with a far-future
    # timestamp; we never tick it, so it costs nothing.
    probe = factory(0)
    return probe.summary()["name"]
