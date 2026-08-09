"""Conversion between device coordinates and output-image pixels."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .map_data import MapData
    from .map_point import MapPoint


@dataclass(frozen=True, slots=True)
class CoordinateSystem:
    """
    Maps device (millimeter) coordinates onto output-image pixels.

    The device grid grows bottom-up while images grow top-down, so the Y
    axis flips around the grid height — the same transform the reference
    parser applies, keeping rendered maps pixel-identical. ``offset``
    shifts every projection by the output border so overlays land inside
    the padded canvas.
    """

    origin_x: float
    origin_y: float
    resolution: float
    grid_height: int
    scale: float
    offset: float = 0.0

    @classmethod
    def for_map(cls, map_data: MapData, scale: float, offset: float = 0.0) -> CoordinateSystem:
        """Build the system for one parsed map at the given output scale."""
        return cls(
            origin_x=map_data.origin_x,
            origin_y=map_data.origin_y,
            resolution=map_data.resolution,
            grid_height=map_data.height,
            scale=scale,
            offset=offset,
        )

    def to_image(self, point: MapPoint) -> tuple[float, float]:
        """Project one device coordinate onto the output image."""
        grid_x = (point.x - self.origin_x) / self.resolution
        grid_y = (point.y - self.origin_y) / self.resolution
        return (
            grid_x * self.scale + self.offset,
            (self.grid_height - grid_y - 1) * self.scale + self.offset,
        )
