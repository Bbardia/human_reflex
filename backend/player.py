"""Player router: assigns detected poses to P1 (left half) and P2 (right half).

Strategy: at each frame, take the two highest-area bounding boxes among detected
poses, sort them by horizontal centroid. Leftmost → P1, rightmost → P2.

This is stateless across frames — we don't track identity. If players physically
swap places, the IDs swap with them. Acceptable for v1 (see spec §14).
"""
from typing import Optional
from backend.pose.types import Pose


def _bbox_area(p: Pose) -> float:
    x0, y0, x1, y1 = p.bbox
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


class PlayerRouter:
    """Assigns up to 2 poses to P1 / P2 by horizontal position."""

    def route(self, poses: list[Pose]) -> tuple[Optional[Pose], Optional[Pose]]:
        if not poses:
            return None, None

        # Take the two largest by bbox area to ignore distant onlookers
        ranked = sorted(poses, key=_bbox_area, reverse=True)[:2]

        if len(ranked) == 1:
            return ranked[0], None

        a, b = ranked
        if a.center_x <= b.center_x:
            return a, b
        return b, a
