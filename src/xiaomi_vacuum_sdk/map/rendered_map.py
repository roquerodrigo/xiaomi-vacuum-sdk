"""One rendered map: the PNG together with the geometry it was drawn from."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .coordinate_system import CoordinateSystem
    from .map_data import MapData


@dataclass(frozen=True, slots=True)
class RenderedMap:
    """
    The finished PNG plus what produced it, so callers need not parse twice.

    ``coordinates`` is the exact projection the renderer used, so a consumer
    can map pixels of ``png`` back onto the device's millimeter frame without
    reimplementing (and drifting from) the transform.
    """

    png: bytes
    map_data: MapData
    coordinates: CoordinateSystem
