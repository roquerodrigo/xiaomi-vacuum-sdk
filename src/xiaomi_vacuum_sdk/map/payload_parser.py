"""Interpretation of the decrypted JSON map payload."""

from __future__ import annotations

import base64
import binascii
import math
import zlib
from typing import TYPE_CHECKING

from .exceptions import MapParseError
from .map_data import MapData
from .map_point import MapPoint
from .quadrilateral import Quadrilateral
from .virtual_wall import VirtualWall

if TYPE_CHECKING:
    from ..json_types import JsonObject, JsonValue

_DEFAULT_RESOLUTION = 50
_QUADRILATERAL_CORNERS = 4
_FLAT_QUADRILATERAL_LENGTH = 8
_FLAT_WALL_LENGTH = 4
_FB_ATTRIBUTE_NO_GO = 0
_FB_ATTRIBUTE_NO_MOP = 1


class MapPayloadParser:
    """
    Builds a typed ``MapData`` from the payload's JSON structures.

    Covers the JSON map format of current Xiaomi MIoT vacuums: a
    base64+zlib pixel grid plus charger/position/path features and the
    forbidden regions in both known shapes (structured ``points`` lists and
    the flat ``fb_point``/``wall_points`` arrays of Dreame-based models).
    """

    def parse(self, payload: JsonObject) -> MapData:
        """Parse one payload, raising ``MapParseError`` when it has no drawable map."""
        width = _integer(payload.get("width"))
        height = _integer(payload.get("height"))
        pixel_data = payload.get("map_data")
        if not width or not height or not isinstance(pixel_data, str):
            raise MapParseError("Failed to parse map payload: no map image published")
        try:
            pixels = zlib.decompress(base64.b64decode(pixel_data))
        except (ValueError, zlib.error, binascii.Error) as error:
            raise MapParseError(f"Failed to decode map pixels: {error}") from error
        if len(pixels) < width * height:
            raise MapParseError(
                f"Failed to decode map pixels: got {len(pixels)} bytes for {width}x{height}"
            )
        return MapData(
            width=width,
            height=height,
            origin_x=_number(payload.get("origin_x")),
            origin_y=_number(payload.get("origin_y")),
            resolution=_number(payload.get("resolution")) or _DEFAULT_RESOLUTION,
            pixels=pixels,
            charger=_parse_charger(payload),
            vacuum=_parse_vacuum(payload),
            path=_parse_path(payload),
            virtual_walls=_parse_virtual_walls(payload),
            no_go_zones=_parse_forbidden_zones(payload, _FB_ATTRIBUTE_NO_GO, "no_go"),
            no_mop_zones=_parse_forbidden_zones(payload, _FB_ATTRIBUTE_NO_MOP, "no_mop"),
            zones=_parse_cleaning_zones(payload),
        )


def _parse_charger(payload: JsonObject) -> MapPoint | None:
    if not payload.get("have_pile"):
        return None
    return MapPoint(
        x=_number(payload.get("pile_x")),
        y=_number(payload.get("pile_y")),
        angle=_yaw_to_degrees(payload.get("pile_yaw")),
    )


def _parse_vacuum(payload: JsonObject) -> MapPoint | None:
    position = payload.get("position")
    if not isinstance(position, dict):
        return None
    return MapPoint(
        x=_number(position.get("x")),
        y=_number(position.get("y")),
        angle=_yaw_to_degrees(position.get("yaw")),
    )


def _parse_path(payload: JsonObject) -> tuple[MapPoint, ...]:
    paths = payload.get("paths")
    points_source: JsonValue = paths.get("points") if isinstance(paths, dict) else paths
    if not isinstance(points_source, list):
        return ()
    return tuple(
        MapPoint(x=_number(point.get("x")), y=_number(point.get("y")))
        for point in points_source
        if isinstance(point, dict)
    )


def _parse_virtual_walls(payload: JsonObject) -> tuple[VirtualWall, ...]:
    walls: list[VirtualWall] = []
    for region in _forbidden_regions(payload):
        corners = _corner_points(region.get("points"))
        if region.get("type") == "wall" and corners is not None:
            walls.append(VirtualWall(corners[0].x, corners[0].y, corners[2].x, corners[2].y))
    for wall in _json_object_list(payload.get("fb_walls")):
        flat = wall.get("wall_points")
        if isinstance(flat, list) and len(flat) == _FLAT_WALL_LENGTH:
            start_x, start_y, end_x, end_y = (_number(value) for value in flat)
            walls.append(VirtualWall(start_x, start_y, end_x, end_y))
    return tuple(walls)


def _parse_forbidden_zones(
    payload: JsonObject, fb_attribute: int, type_name: str
) -> tuple[Quadrilateral, ...]:
    zones: list[Quadrilateral] = []
    for region in _forbidden_regions(payload):
        flat = region.get("fb_point")
        if flat is not None:
            if (
                isinstance(flat, list)
                and len(flat) == _FLAT_QUADRILATERAL_LENGTH
                and region.get("fb_attr", _FB_ATTRIBUTE_NO_GO) == fb_attribute
            ):
                coordinates = [_number(value) for value in flat]
                zones.append(Quadrilateral(*coordinates))
            continue
        corners = _corner_points(region.get("points"))
        if region.get("type") == type_name and corners is not None:
            zones.append(
                Quadrilateral(
                    corners[0].x,
                    corners[0].y,
                    corners[1].x,
                    corners[1].y,
                    corners[2].x,
                    corners[2].y,
                    corners[3].x,
                    corners[3].y,
                )
            )
    return tuple(zones)


def _parse_cleaning_zones(payload: JsonObject) -> tuple[Quadrilateral, ...]:
    configuration = payload.get("current_cleaning_config")
    if not isinstance(configuration, dict):
        return ()
    return tuple(
        Quadrilateral.from_rectangle(
            _number(zone.get("x1")),
            _number(zone.get("y1")),
            _number(zone.get("x2")),
            _number(zone.get("y2")),
        )
        for zone in _json_object_list(configuration.get("zones"))
    )


def _forbidden_regions(payload: JsonObject) -> list[JsonObject]:
    return _json_object_list(payload.get("fb_regions"))


def _json_object_list(value: JsonValue) -> list[JsonObject]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _corner_points(points: JsonValue) -> list[MapPoint] | None:
    if not isinstance(points, list) or len(points) != _QUADRILATERAL_CORNERS:
        return None
    corners: list[MapPoint] = []
    for point in points:
        if not isinstance(point, dict):
            return None
        corners.append(MapPoint(x=_number(point.get("x")), y=_number(point.get("y"))))
    return corners


def _number(value: JsonValue) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0.0
    return float(value)


def _integer(value: JsonValue) -> int:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0
    return int(value)


def _yaw_to_degrees(yaw: JsonValue) -> float:
    """
    Normalize the payload's yaw to degrees.

    Firmwares disagree on the unit: values within ±2π are radians, values
    beyond 180 are centi-degrees, the rest are already degrees.
    """
    value = _number(yaw)
    if abs(value) <= 2 * math.pi + 0.001:
        return value * 180.0 / math.pi
    if abs(value) > 180.0:  # noqa: PLR2004 -- the 180° threshold is the unit heuristic itself
        return (value / 100.0) % 180.0
    return value % 180.0
