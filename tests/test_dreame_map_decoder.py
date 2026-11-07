"""Dreame map decoding: envelope, frame header, pixels, rooms and restrictions."""

from __future__ import annotations

import io
import json

import pytest
from PIL import Image

from dreame_fixtures import (
    HEIGHT,
    LEFT,
    RESOLUTION,
    TOP,
    TRAILER,
    WIDTH,
    encode,
    envelope,
    frame,
    name,
)
from xiaomi_vacuum_sdk import (
    DreameMapDecoder,
    MapDecryptError,
    MapError,
    MapParseError,
    MapPoint,
    MapRenderer,
    MapSegment,
    Quadrilateral,
    RenderOptions,
    VirtualWall,
)


def decode(blob: bytes):
    return DreameMapDecoder().decode(blob)


def test_decodes_the_saved_map_envelope():
    data = decode(envelope(encode(frame(TRAILER))))
    assert (data.width, data.height) == (WIDTH, HEIGHT)
    assert (data.origin_x, data.origin_y, data.resolution) == (LEFT, TOP, RESOLUTION)
    assert data.charger == MapPoint(-40, 10, 90)
    assert data.vacuum is None
    assert data.path == ()
    assert data.zones == ()


def test_pixels_follow_the_map_data_convention():
    """Segment ids shift into the room range; wall-flagged cells become walls."""
    data = decode(encode(frame()).encode())
    assert data.pixels == bytes([255, 255, 255, 255, 3, 3, 4, 255, 0, 0, 0, 0])


def test_reserved_segment_values_are_floor_not_rooms():
    """61 is the last room id; 62 and 63 are reserved and drawn as plain floor."""
    pixels = bytes([0x3D, 0x3E, 0x3F, 0x01]) * HEIGHT
    assert decode(encode(frame(pixels=pixels)).encode()).pixels[:4] == bytes([63, 1, 1, 3])


def test_every_segment_sorted_by_id_unnamed_ones_included():
    data = decode(envelope(encode(frame(TRAILER))))
    assert data.segments == (
        MapSegment(1, "Living room", 0),
        MapSegment(2, "Cozinha"),
        MapSegment(4, ""),
    )


def test_names_that_are_not_base64_utf8_count_as_unnamed():
    """Names are always base64; a plain word must not be decoded into garbage."""
    trailer = {
        "seg_inf": {
            "3": {"name": "Not base64!"},
            "5": {"name": "//79"},  # valid base64, not UTF-8
            "6": {"name": name("Kids"), "type": True},
            "x": {},
        }
    }
    segments = decode(encode(frame(trailer)).encode()).segments
    assert segments == (MapSegment(3, ""), MapSegment(5, ""), MapSegment(6, "Kids"))


def test_restrictions_become_walls_and_zones():
    data = decode(envelope(encode(frame(TRAILER))))
    assert data.virtual_walls == (VirtualWall(0, 0, 100, 0),)
    assert data.no_go_zones == (Quadrilateral.from_rectangle(-100, -50, 0, 0),)
    assert data.no_mop_zones == (Quadrilateral.from_rectangle(10, 20, 30, 40),)


def test_live_frame_carries_the_robot_position():
    data = decode(
        encode(
            frame(
                robot_x=120, robot_y=-80, robot_angle=45, charger_x=0, charger_y=0, charger_angle=0
            )
        ).encode()
    )
    assert data.vacuum == MapPoint(120, -80, 45)
    assert data.charger is None


def test_frame_without_trailer_has_no_segments():
    data = decode(encode(frame()).encode())
    assert data.segments == ()
    assert data.no_go_zones == ()


def test_envelope_without_current_id_uses_the_first_map():
    blob = json.dumps({"mapstr": [{"id": 3, "map": encode(frame(TRAILER))}]}).encode()
    assert decode(blob).segments[0] == MapSegment(1, "Living room", 0)


@pytest.mark.parametrize(
    "blob",
    [
        "café".encode(),
        b"{not json",
        b'{"mapstr": []}',
        b'{"mapstr": [{"id": 0}]}',
        b"[1]",
        b"@@@@",
        b"AAAA",
    ],
    ids=["not-ascii", "bad-envelope", "empty", "no-map", "array", "not-base64", "not-zlib"],
)
def test_undecodable_blobs_raise_decrypt_errors(blob):
    with pytest.raises(MapDecryptError):
        decode(blob)


def test_encrypted_frames_are_refused():
    with pytest.raises(MapDecryptError, match="encrypted"):
        decode(encode(frame(TRAILER), key="secret").encode())


@pytest.mark.parametrize(
    "raw_frame",
    [
        b"tiny",
        frame(width=0),
        frame(resolution=0),
        frame(pixels=b"\x00"),
        frame() + b"\xff\xfe",
        frame() + b"{broken",
    ],
    ids=["short", "no-width", "no-resolution", "truncated", "not-utf8", "bad-json"],
)
def test_undrawable_frames_raise_parse_errors(raw_frame):
    with pytest.raises(MapParseError):
        decode(encode(raw_frame).encode())


def test_errors_share_the_map_root():
    with pytest.raises(MapError):
        decode(b"AAAA")


def test_trailer_that_is_not_an_object_is_ignored():
    data = decode(encode(frame() + b"[1, 2]").encode())
    assert data.segments == ()


def test_decoded_map_renders_through_the_stock_pipeline():
    data = decode(envelope(encode(frame(TRAILER))))
    rendered = MapRenderer(RenderOptions(border=0, scale=1, layers=frozenset())).render_map_data(
        data
    )
    image = Image.open(io.BytesIO(rendered.png)).convert("RGBA")
    assert image.size == (WIDTH, HEIGHT)
    assert rendered.map_data is data
    # Grid row 1 (room 1 at x 0-1) is the middle image row after the flip.
    assert image.getpixel((0, 1)) != image.getpixel((0, 0))
    assert image.getpixel((0, 0))[3] == 0  # top row: outside, transparent
    assert rendered.coordinates.to_device(0, HEIGHT - 1) == MapPoint(LEFT, TOP)


def test_room_name_helper_round_trips():
    assert decode(encode(frame({"seg_inf": {"9": {"name": name("Sala")}}})).encode()).segments == (
        MapSegment(9, "Sala"),
    )
