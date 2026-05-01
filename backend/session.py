"""Top-level session state machine: TITLE -> COUNTDOWN -> GAME -> SUMMARY -> TITLE.

Player 1 controls the menus by raising both hands above their head for 2s.
This first-plan iteration only runs the Touch the Circle game; later plans
add Goalie / Pose Simon / Laser Limbo and the multi-game leaderboard.
"""
from typing import Optional
from backend.config import CONFIG
from backend.gestures import is_hands_up, GestureHold
from backend.games.touch_circle import TouchCircleGame
from backend.pose.types import Pose


SCREEN_TITLE = "title"
SCREEN_COUNTDOWN = "countdown"
SCREEN_GAME = "game"
SCREEN_SUMMARY = "summary"

COUNTDOWN_MS = 4000  # 3 -> 2 -> 1 -> GO
SUMMARY_MIN_HOLD_MS = 1500  # ignore hands-up for the first 1.5s of summary


class Session:
    def __init__(self, now_ms: int = 0):
        self._screen = SCREEN_TITLE
        self._screen_entered_ms = now_ms
        self._gesture_hold = GestureHold(hold_ms=CONFIG.gesture.hold_ms)
        self._game: Optional[TouchCircleGame] = None
        self._countdown_started_ms: Optional[int] = None
        self._latest_summary: Optional[dict] = None

    # ---- private transitions ----

    def _enter_title(self, now_ms: int) -> None:
        self._screen = SCREEN_TITLE
        self._screen_entered_ms = now_ms
        self._gesture_hold.reset()
        self._game = None
        self._latest_summary = None
        self._countdown_started_ms = None

    def _enter_countdown(self, now_ms: int) -> None:
        self._screen = SCREEN_COUNTDOWN
        self._screen_entered_ms = now_ms
        self._countdown_started_ms = now_ms
        self._gesture_hold.reset()

    def _enter_game(self, now_ms: int) -> None:
        self._screen = SCREEN_GAME
        self._screen_entered_ms = now_ms
        self._game = TouchCircleGame(
            now_ms=now_ms, config=CONFIG.touch_circle, seed=now_ms
        )

    def _enter_summary(self, now_ms: int, summary: dict) -> None:
        self._screen = SCREEN_SUMMARY
        self._screen_entered_ms = now_ms
        self._gesture_hold.reset()
        self._latest_summary = summary

    # ---- main tick ----

    def tick(self, now_ms: int, p1: Optional[Pose], p2: Optional[Pose]) -> None:
        if self._screen == SCREEN_TITLE:
            self._tick_title(now_ms, p1)
        elif self._screen == SCREEN_COUNTDOWN:
            self._tick_countdown(now_ms)
        elif self._screen == SCREEN_GAME:
            self._tick_game(now_ms, p1, p2)
        elif self._screen == SCREEN_SUMMARY:
            self._tick_summary(now_ms, p1)

    def _tick_title(self, now_ms: int, p1: Optional[Pose]) -> None:
        active = p1 is not None and is_hands_up(p1)
        if self._gesture_hold.update(active=active, now_ms=now_ms):
            self._enter_countdown(now_ms)

    def _tick_countdown(self, now_ms: int) -> None:
        if now_ms - (self._countdown_started_ms or now_ms) >= COUNTDOWN_MS:
            self._enter_game(now_ms)

    def _tick_game(self, now_ms: int, p1: Optional[Pose], p2: Optional[Pose]) -> None:
        assert self._game is not None
        self._game.tick(now_ms, p1, p2)
        if self._game.is_done():
            self._enter_summary(now_ms, self._game.summary())

    def _tick_summary(self, now_ms: int, p1: Optional[Pose]) -> None:
        if now_ms - self._screen_entered_ms < SUMMARY_MIN_HOLD_MS:
            # Ignore gestures for the first 1.5s so the result is readable
            return
        active = p1 is not None and is_hands_up(p1)
        if self._gesture_hold.update(active=active, now_ms=now_ms):
            self._enter_title(now_ms)

    # ---- serialisation ----

    def to_dict(self, now_ms: int) -> dict:
        out = {
            "screen": self._screen,
            "gesture_progress": self._gesture_hold.progress(now_ms),
        }
        if self._screen == SCREEN_COUNTDOWN and self._countdown_started_ms is not None:
            out["countdown_ms_total"] = COUNTDOWN_MS
        if self._screen == SCREEN_GAME and self._game is not None:
            out["game"] = self._game.to_dict()
        if self._screen == SCREEN_SUMMARY:
            out["summary"] = self._latest_summary
        return out

    def snapshot(self, now_ms: int, p1: Optional[Pose], p2: Optional[Pose]) -> dict:
        """Build the wire-format snapshot for the WebSocket."""
        out = self.to_dict(now_ms)
        if self._screen == SCREEN_COUNTDOWN and self._countdown_started_ms is not None:
            out["countdown_remaining_ms"] = max(
                0, COUNTDOWN_MS - (now_ms - self._countdown_started_ms)
            )
        out["players"] = {
            "p1": p1.to_dict() if p1 is not None else None,
            "p2": p2.to_dict() if p2 is not None else None,
        }
        return out
