"""Decoding of the Dreame cloud map blob into :class:`MapData`."""

from __future__ import annotations

import base64
import binascii
import json
import logging
import struct
import zlib
from typing import TYPE_CHECKING

from .exceptions import MapDecryptError, MapParseError
from .map_data import MapData
from .map_point import MapPoint
from .map_segment import MapSegment
from .quadrilateral import Quadrilateral
from .virtual_wall import VirtualWall

if TYPE_CHECKING:
    from ..json_types import JsonObject, JsonValue

log: logging.Logger = logging.getLogger("xiaomi_vacuum_sdk.map")

# Little-endian frame header: map id, frame id, frame type, robot x/y/angle,
# charger x/y/angle, resolution, width, height, left, top.
_HEADER = struct.Struct("<hhBhhhhhhhhhhh")
_SEGMENT_MASK = 0x3F
_WALL_FLAG = 0x80
# Segment ids 1-61 shift onto MapData's room values 3-63 (1 and 2 are floor).
_ROOM_PIXEL_OFFSET = 2
# Dreame reserves the top two segment values (unassigned floor, a segment
# still being created); they are floor, not rooms.
_RESERVED_SEGMENTS = frozenset({62, 63})
_FLOOR_PIXEL = 1
_WALL_PIXEL = 255
_RECTANGLE_SIZE = 4


class DreameMapDecoder:
    """
    Decodes the map blob of Dreame-built vacuums (e.g. ``xiaomi.vacuum.c102gl``).

    The cloud object is either a bare frame or a saved-map envelope
    ``{"mapstr": [{"id", "map", ...}], "curr_id"}``. A frame is url-safe
    base64 of a zlib stream: a 27-byte header, ``width * height`` pixel
    bytes, then a JSON trailer with the rooms (``seg_inf``) and the
    restrictions (``vw``). Each pixel holds a segment id in its low six bits
    and a wall flag in its top bit; the decoder translates them to the
    :class:`MapData` pixel convention so the stock renderer draws them.
    """

    def decode(self, blob: bytes) -> MapData:
        """Decode one Dreame map blob, raising a :class:`MapError` subclass on failure."""
        frame = _inflate(_frame_text(blob))
        if len(frame) < _HEADER.size:
            msg = f"Failed to parse map: frame has {len(frame)} bytes, header needs {_HEADER.size}"
            raise MapParseError(msg)
        (_, _, _, robot_x, robot_y, robot_angle, charger_x, charger_y, charger_angle,
         resolution, width, height, left, top) = _HEADER.unpack_from(frame)  # fmt: skip
        pixel_end = _HEADER.size + width * height
        if width <= 0 or height <= 0 or resolution <= 0 or len(frame) < pixel_end:
            msg = f"Failed to parse map: no drawable {width}x{height} grid in the frame"
            raise MapParseError(msg)
        trailer = _trailer(frame[pixel_end:])
        restrictions = _object(trailer.get("vw"))
        log.debug("Dreame map frame: %sx%s at %s mm", width, height, resolution)
        return MapData(
            width=width,
            height=height,
            origin_x=left,
            origin_y=top,
            resolution=resolution,
            pixels=bytes(_pixel(value) for value in frame[_HEADER.size : pixel_end]),
            charger=_position(charger_x, charger_y, charger_angle),
            vacuum=_position(robot_x, robot_y, robot_angle),
            path=(),
            virtual_walls=tuple(
                VirtualWall(*line) for line in _rectangles(restrictions.get("line"))
            ),
            no_go_zones=tuple(
                Quadrilateral.from_rectangle(*rect)
                for rect in _rectangles(restrictions.get("rect"))
            ),
            no_mop_zones=tuple(
                Quadrilateral.from_rectangle(*rect) for rect in _rectangles(restrictions.get("mop"))
            ),
            zones=(),
            segments=_segments(trailer.get("seg_inf")),
        )


def _frame_text(blob: bytes) -> str:
    try:
        text = blob.decode("ascii").strip()
    except UnicodeDecodeError as exception:
        msg = "Failed to decode map: blob is not ASCII"
        raise MapDecryptError(msg) from exception
    if not text.startswith("{"):
        return text
    try:
        envelope: JsonValue = json.loads(text)
    except json.JSONDecodeError as exception:
        msg = f"Failed to decode map: invalid envelope: {exception}"
        raise MapDecryptError(msg) from exception
    maps = [m for m in _list(_object(envelope).get("mapstr")) if isinstance(m, dict)]
    current = next((m for m in maps if m.get("id") == _object(envelope).get("curr_id")), None)
    if current is None and maps:
        current = maps[0]
    frame = current.get("map") if current is not None else None
    if not isinstance(frame, str):
        msg = "Failed to decode map: envelope holds no map"
        raise MapDecryptError(msg)
    return frame


def _inflate(text: str) -> bytes:
    encoded, _, key = text.replace("_", "/").replace("-", "+").partition(",")
    if key:
        # A ",<key>" suffix marks an AES-encrypted frame whose IV is per model.
        msg = "Failed to decode map: encrypted Dreame maps are not supported"
        raise MapDecryptError(msg)
    try:
        return zlib.decompress(base64.b64decode(encoded + "=" * (-len(encoded) % 4)))
    except (binascii.Error, zlib.error) as exception:
        msg = f"Failed to decode map: {exception}"
        raise MapDecryptError(msg) from exception


def _trailer(data: bytes) -> JsonObject:
    if not data:
        return {}
    try:
        trailer: JsonValue = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exception:
        msg = f"Failed to parse map: invalid metadata trailer: {exception}"
        raise MapParseError(msg) from exception
    return _object(trailer)


def _pixel(value: int) -> int:
    segment = value & _SEGMENT_MASK
    if value & _WALL_FLAG:
        return _WALL_PIXEL
    if segment == 0:
        return 0
    if segment in _RESERVED_SEGMENTS:
        return _FLOOR_PIXEL
    return segment + _ROOM_PIXEL_OFFSET


def _position(x: int, y: int, angle: int) -> MapPoint | None:
    # Saved maps zero the whole position instead of omitting it.
    if x == 0 and y == 0 and angle == 0:
        return None
    return MapPoint(x, y, angle)


def _rectangles(value: JsonValue) -> list[tuple[float, float, float, float]]:
    rectangles: list[tuple[float, float, float, float]] = []
    for entry in _list(value):
        numbers = [n for n in _list(entry) if isinstance(n, int | float)]
        if len(numbers) >= _RECTANGLE_SIZE:
            rectangles.append((numbers[0], numbers[1], numbers[2], numbers[3]))
    return rectangles


def _segments(value: JsonValue) -> tuple[MapSegment, ...]:
    segments: list[MapSegment] = []
    for key, info in _object(value).items():
        if not key.isdigit():
            continue
        details = _object(info)
        room_type = details.get("type")
        segments.append(
            MapSegment(
                int(key),
                _segment_name(details.get("name")),
                room_type
                if isinstance(room_type, int) and not isinstance(room_type, bool)
                else None,
            )
        )
    return tuple(sorted(segments, key=lambda segment: segment.id))


def _segment_name(value: JsonValue) -> str:
    # The app always stores names base64-encoded (a typed "kids" arrives as
    # "a2lkcw=="), so anything that does not decode is treated as no name
    # rather than guessed at as plain text.
    if not isinstance(value, str) or not value:
        return ""
    try:
        return base64.b64decode(value, validate=True).decode("utf-8").strip()
    except (binascii.Error, UnicodeDecodeError):
        log.debug("Dreame segment name is not base64 UTF-8; treating it as unnamed")
        return ""


def _object(value: JsonValue) -> JsonObject:
    return value if isinstance(value, dict) else {}


def _list(value: JsonValue) -> list[JsonValue]:
    return value if isinstance(value, list) else []
