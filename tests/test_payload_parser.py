"""Payload parsing tests over the golden payload and its edge cases."""

from __future__ import annotations

import math

import pytest

from map_fixtures import GOLDEN_PAYLOAD
from xiaomi_vacuum_sdk.map.exceptions import MapParseError
from xiaomi_vacuum_sdk.map.payload_parser import MapPayloadParser, _yaw_to_degrees
from xiaomi_vacuum_sdk.map.quadrilateral import Quadrilateral
from xiaomi_vacuum_sdk.map.virtual_wall import VirtualWall


def test_parses_golden_payload_structure():
    map_data = MapPayloadParser().parse(GOLDEN_PAYLOAD)
    assert map_data.width == 8
    assert map_data.height == 8
    assert map_data.origin_x == -200
    assert map_data.origin_y == -200
    assert map_data.resolution == 50
    assert len(map_data.pixels) == 64

    assert map_data.charger is not None
    assert (map_data.charger.x, map_data.charger.y) == (-100, -100)
    assert map_data.charger.angle == 90.0

    assert map_data.vacuum is not None
    assert (map_data.vacuum.x, map_data.vacuum.y) == (0, 0)
    assert map_data.vacuum.angle == 45.0

    assert [(point.x, point.y) for point in map_data.path] == [(-100, -100), (0, -50), (50, 0)]

    assert map_data.virtual_walls == (VirtualWall(-150, 100, 150, 100),)
    assert map_data.no_go_zones == (Quadrilateral(-150, -150, -120, -150, -120, -120, -150, -120),)
    assert map_data.no_mop_zones == (Quadrilateral(60, 60, 90, 60, 90, 90, 60, 90),)
    assert map_data.zones == (Quadrilateral.from_rectangle(0, 0, 80, 80),)


def test_missing_image_raises_parse_error():
    with pytest.raises(MapParseError, match="no map image"):
        MapPayloadParser().parse({"width": 8, "height": 8})


def test_invalid_pixel_encoding_raises_parse_error():
    payload = {"width": 8, "height": 8, "map_data": "not-base64-zlib!"}
    with pytest.raises(MapParseError, match="Failed to decode"):
        MapPayloadParser().parse(payload)


def test_truncated_pixels_raise_parse_error():
    import base64
    import zlib

    payload = {
        "width": 8,
        "height": 8,
        "map_data": base64.b64encode(zlib.compress(b"\x00" * 10)).decode(),
    }
    with pytest.raises(MapParseError, match="got 10 bytes"):
        MapPayloadParser().parse(payload)


def test_payload_without_features_parses_empty():
    import base64
    import zlib

    payload = {
        "width": 2,
        "height": 2,
        "map_data": base64.b64encode(zlib.compress(b"\x00\x01\x02\x40")).decode(),
    }
    map_data = MapPayloadParser().parse(payload)
    assert map_data.charger is None
    assert map_data.vacuum is None
    assert map_data.path == ()
    assert map_data.virtual_walls == ()
    assert map_data.no_go_zones == ()
    assert map_data.no_mop_zones == ()
    assert map_data.zones == ()
    assert map_data.resolution == 50


def test_yaw_radians_are_converted():
    assert _yaw_to_degrees(math.pi) == pytest.approx(180.0)
    assert _yaw_to_degrees(math.pi / 2) == pytest.approx(90.0)


def test_yaw_centidegrees_are_converted():
    assert _yaw_to_degrees(2470) == pytest.approx(24.7)
    assert _yaw_to_degrees(9000) == pytest.approx(90.0)


def test_yaw_plain_degrees_pass_through():
    assert _yaw_to_degrees(150) == pytest.approx(150.0)


def test_yaw_invalid_defaults_to_zero():
    assert _yaw_to_degrees(None) == 0.0
    assert _yaw_to_degrees("north") == 0.0
