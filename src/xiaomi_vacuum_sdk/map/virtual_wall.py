"""A user-defined virtual wall."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VirtualWall:
    """A straight line the vacuum will not cross, in device coordinates."""

    start_x: float
    start_y: float
    end_x: float
    end_y: float
