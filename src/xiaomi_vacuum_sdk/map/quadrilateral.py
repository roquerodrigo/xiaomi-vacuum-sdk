"""A four-corner map region."""

from __future__ import annotations

from dataclasses import dataclass

from .map_point import MapPoint


@dataclass(frozen=True, slots=True)
class Quadrilateral:
    """A four-corner region (no-go zone, no-mop zone or cleaning zone)."""

    x1: float
    y1: float
    x2: float
    y2: float
    x3: float
    y3: float
    x4: float
    y4: float

    @classmethod
    def from_rectangle(cls, left: float, top: float, right: float, bottom: float) -> Quadrilateral:
        """Build from two opposite corners."""
        return cls(left, top, right, top, right, bottom, left, bottom)

    def corners(self) -> tuple[MapPoint, MapPoint, MapPoint, MapPoint]:
        """Return the four corners, in declaration order."""
        return (
            MapPoint(self.x1, self.y1),
            MapPoint(self.x2, self.y2),
            MapPoint(self.x3, self.y3),
            MapPoint(self.x4, self.y4),
        )
