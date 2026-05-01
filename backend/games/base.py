"""Game ABC. A game owns its state machine and produces serialisable state for the frontend."""
from abc import ABC, abstractmethod
from typing import Optional
from backend.pose.types import Pose


class Game(ABC):
    """Lifecycle: __init__ → tick(...) repeatedly → is_done() → summary().

    Implementations must be deterministic given the same sequence of inputs
    (with random_seed for any randomness). This keeps tests sane.
    """

    @abstractmethod
    def tick(self, now_ms: int, p1: Optional[Pose], p2: Optional[Pose]) -> None:
        ...

    @abstractmethod
    def is_done(self) -> bool:
        ...

    @abstractmethod
    def winner(self) -> Optional[int]:
        """1, 2, or None for draw / undecided."""
        ...

    @abstractmethod
    def to_dict(self) -> dict:
        """Snapshot for WebSocket. Include enough that the frontend can render."""
        ...

    @abstractmethod
    def summary(self) -> dict:
        """End-of-game summary for the leaderboard / per-game summary screen."""
        ...
