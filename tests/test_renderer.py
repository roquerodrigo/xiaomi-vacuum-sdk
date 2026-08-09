"""Rendering tests: PNG structure, colors and layer filtering."""

from __future__ import annotations

import io

from PIL import Image

from map_fixtures import DEVICE_ID, GOLDEN_BLOB, MODEL
from xiaomi_vacuum_sdk import Layer, MapRenderer, Palette, RenderOptions

FLOOR = (92, 110, 84, 255)
OUTSIDE = (250, 249, 246, 0)
ROOM_3_COLOR = (186, 210, 206, 255)
ROOM_4_COLOR = (214, 196, 168, 255)


def render_image(**option_overrides):
    options = RenderOptions(**option_overrides)
    png = MapRenderer(options).render(GOLDEN_BLOB, model=MODEL, device_id=DEVICE_ID)
    return Image.open(io.BytesIO(png)).convert("RGBA")


def test_renders_png_at_scaled_dimensions():
    image = render_image()
    assert image.size == (64, 64)


def test_grid_rows_are_flipped_and_colored():
    image = render_image(layers=frozenset())
    # Grid row 7 (all outside) is the top image row; grid row 1 is a wall run.
    assert image.getpixel((4, 4)) == OUTSIDE
    assert image.getpixel((12, 52)) == FLOOR  # grid (1, 1) is a wall — same theme color as floor
    assert image.getpixel((20, 44)) == ROOM_3_COLOR  # grid (2, 2) holds room id 3
    assert image.getpixel((36, 44)) == ROOM_4_COLOR  # grid (4, 2) holds room id 4
    assert image.getpixel((20, 28)) == FLOOR  # grid (2, 4) holds free-space value 1


def test_vacuum_layer_draws_over_the_floor():
    bare = render_image(layers=frozenset())
    with_vacuum = render_image(layers=frozenset({Layer.VACUUM_POSITION}))
    # The vacuum sits at device (0, 0) -> grid (4, 4) -> image (32, 24).
    assert bare.getpixel((32, 24)) != with_vacuum.getpixel((32, 24))
    assert with_vacuum.getpixel((32, 24)) == (255, 254, 250, 255)


def test_charger_layer_draws_translucent_dock():
    with_charger = render_image(layers=frozenset({Layer.CHARGER}))
    bare = render_image(layers=frozenset())
    # The charger sits at device (-100, -100) -> grid (2, 2) -> image (16, 40).
    assert with_charger.getpixel((16, 40)) != bare.getpixel((16, 40))


def test_all_layers_change_the_image():
    bare = render_image(layers=frozenset())
    for layer in Layer:
        assert render_image(layers=frozenset({layer})).tobytes() != bare.tobytes(), layer


def test_custom_palette_changes_floor_color():
    image = render_image(palette=Palette(floor=(1, 2, 3)), layers=frozenset())
    assert image.getpixel((20, 28)) == (1, 2, 3, 255)


def test_scale_one_keeps_native_dimensions():
    image = render_image(scale=1.0, layers=frozenset())
    assert image.size == (8, 8)
