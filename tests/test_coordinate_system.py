"""Coordinate-system tests: the device ↔ image projection and its inverse."""

from __future__ import annotations

import pytest

from xiaomi_vacuum_sdk import CoordinateSystem, MapPoint

SYSTEM = CoordinateSystem(
    origin_x=-2000.0,
    origin_y=-1500.0,
    resolution=50.0,
    grid_height=64,
    scale=8.0,
    offset=12.0,
)


def test_to_image_flips_the_y_axis_and_applies_the_offset():
    assert SYSTEM.to_image(MapPoint(-2000.0, -1500.0)) == (12.0, 516.0)


def test_to_device_inverts_to_image():
    for point in (MapPoint(0.0, 0.0), MapPoint(-1975.0, 320.5), MapPoint(1234.0, -999.0)):
        x, y = SYSTEM.to_image(point)
        device_point = SYSTEM.to_device(x, y)
        assert device_point.x == pytest.approx(point.x)
        assert device_point.y == pytest.approx(point.y)


def test_to_device_without_scaling_or_border():
    system = CoordinateSystem(origin_x=0.0, origin_y=0.0, resolution=10.0, grid_height=4, scale=1.0)
    # Image row 0 is the top, which is grid row 3 (grid_height - 1).
    assert system.to_device(0.0, 0.0) == MapPoint(0.0, 30.0)
    assert system.to_device(2.0, 3.0) == MapPoint(20.0, 0.0)
