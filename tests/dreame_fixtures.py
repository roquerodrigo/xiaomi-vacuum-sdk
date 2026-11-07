"""Synthetic Dreame map blobs: a tiny two-room frame built from the format."""

from __future__ import annotations

import base64
import json
import struct
import zlib

WIDTH = 4
HEIGHT = 3
RESOLUTION = 50
LEFT = -100
TOP = -50
# Bottom row first: wall, room 1, room 2 with a wall-flagged edge, outside.
PIXELS = bytes([0x80, 0x80, 0x80, 0x80, 0x01, 0x01, 0x02, 0x82, 0x00, 0x00, 0x00, 0x00])


_HEADER_DEFAULTS = {
    "robot_x": 0,
    "robot_y": 0,
    "robot_angle": 0,
    "charger_x": -40,
    "charger_y": 10,
    "charger_angle": 90,
    "resolution": RESOLUTION,
    "width": WIDTH,
    "height": HEIGHT,
}


def frame(trailer: dict | None = None, *, pixels: bytes = PIXELS, **header: int) -> bytes:
    """Raw (inflated) Dreame frame: header, pixels and JSON trailer."""
    fields = _HEADER_DEFAULTS | header
    packed = struct.pack(
        "<hhBhhhhhhhhhhh",
        1,
        0,
        ord("I"),
        *(fields[key] for key in _HEADER_DEFAULTS),
        LEFT,
        TOP,
    )
    tail = b"" if trailer is None else json.dumps(trailer).encode()
    return packed + pixels + tail


def encode(raw_frame: bytes, *, key: str = "") -> str:
    """Url-safe base64 of the zlib frame, the way the cloud stores it."""
    text = base64.b64encode(zlib.compress(raw_frame)).decode()
    text = text.replace("/", "_").replace("+", "-").rstrip("=")
    return f"{text},{key}" if key else text


def envelope(encoded: str, *, curr_id: int = 7) -> bytes:
    """Saved-map envelope whose current entry holds ``encoded``."""
    maps = [{"id": 0, "map": "not-the-current-map"}, {"id": 7, "map": encoded}]
    return json.dumps({"mapstr": maps, "curr_id": curr_id}).encode()


def name(text: str) -> str:
    """Base64 room name, as ``seg_inf`` stores it."""
    return base64.b64encode(text.encode()).decode()


TRAILER = {
    "seg_inf": {
        "2": {"name": name("Cozinha")},
        "1": {"name": name("Living room"), "type": 0},
        "4": {"nei_id": [1]},
    },
    "vw": {
        "line": [[0, 0, 100, 0]],
        "rect": [[-100, -50, 0, 0], [1, 2]],
        "mop": [[10, 20, 30, 40]],
    },
}
