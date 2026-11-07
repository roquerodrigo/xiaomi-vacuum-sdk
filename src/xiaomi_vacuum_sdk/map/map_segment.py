"""A room (segment) of a map."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MapSegment:
    """
    One room as the vacuum knows it, keyed by the id room-clean commands take.

    ``name`` is empty when the user never named the segment: unnamed segments
    are kept so consumers decide how to label or skip them. ``room_type`` is
    the firmware's room-type code when the payload carries one.
    """

    id: int
    name: str
    room_type: int | None = None
