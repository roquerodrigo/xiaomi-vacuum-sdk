"""Aggregate of everything parsed from one map payload."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .map_point import MapPoint
    from .quadrilateral import Quadrilateral
    from .virtual_wall import VirtualWall


@dataclass(frozen=True, slots=True)
class MapData:
    """
    One parsed map: the floor grid plus every feature the renderer draws.

    ``pixels`` is the raw grid, row 0 at the bottom, one byte per cell:
    ``0`` outside, ``1``/``2`` floor, ``3``-``63`` a room, anything else a
    wall. Positions are in device (millimeter) coordinates anchored at
    ``origin_x``/``origin_y`` with ``resolution`` millimeters per cell.
    """

    width: int
    height: int
    origin_x: float
    origin_y: float
    resolution: float
    pixels: bytes
    charger: MapPoint | None
    vacuum: MapPoint | None
    path: tuple[MapPoint, ...]
    virtual_walls: tuple[VirtualWall, ...]
    no_go_zones: tuple[Quadrilateral, ...]
    no_mop_zones: tuple[Quadrilateral, ...]
    zones: tuple[Quadrilateral, ...]
