"""A named room (segment) of a map."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MapSegment:
    """One room as the vacuum knows it: the id room-clean commands take, and its name."""

    id: int
    name: str
