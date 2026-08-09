"""A position on the map."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MapPoint:
    """A position in device (millimeter) coordinates, with an optional heading in degrees."""

    x: float
    y: float
    angle: float | None = None
