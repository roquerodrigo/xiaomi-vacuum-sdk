"""Rendering tests: PNG structure, colors, border and layer filtering."""

from __future__ import annotations

import io

from PIL import Image

from map_fixtures import DEVICE_ID, GOLDEN_BLOB, MODEL
from xiaomi_vacuum_sdk import Layer, MapRenderer, Palette, RenderOptions

FLOOR = (92, 110, 84, 255)
OUTSIDE = (250, 249, 246, 0)
ROOM_3_COLOR = (186, 210, 206, 255)
ROOM_4_COLOR = (214, 196, 168, 255)
BORDER = 12


def render_image(**option_overrides):
    options = RenderOptions(**option_overrides)
    png = MapRenderer(options).render(GOLDEN_BLOB, model=MODEL, device_id=DEVICE_ID)
    return Image.open(io.BytesIO(png)).convert("RGBA")


def test_renders_png_with_default_border():
    image = render_image()
    assert image.size == (64 + BORDER * 2, 64 + BORDER * 2)


def test_border_zero_keeps_raw_dimensions():
    image = render_image(border=0)
    assert image.size == (64, 64)


def test_border_area_uses_outside_color():
    image = render_image()
    assert image.getpixel((5, 5)) == OUTSIDE
    assert image.getpixel((image.width - 5, image.height - 5)) == OUTSIDE


def test_grid_rows_are_flipped_and_colored():
    image = render_image(layers=frozenset())
    # Grid row 7 (all outside) is the top image row; grid row 1 is a wall run.
    assert image.getpixel((BORDER + 4, BORDER + 4)) == OUTSIDE
    assert image.getpixel((BORDER + 12, BORDER + 52)) == FLOOR  # grid (1, 1): wall, theme color
    assert image.getpixel((BORDER + 20, BORDER + 44)) == ROOM_3_COLOR  # grid (2, 2): room id 3
    assert image.getpixel((BORDER + 36, BORDER + 44)) == ROOM_4_COLOR  # grid (4, 2): room id 4
    assert image.getpixel((BORDER + 20, BORDER + 28)) == FLOOR  # grid (2, 4): free-space value 1


def test_vacuum_layer_draws_over_the_floor():
    bare = render_image(layers=frozenset())
    with_vacuum = render_image(layers=frozenset({Layer.VACUUM_POSITION}))
    # The vacuum sits at device (0, 0) -> grid (4, 4) -> image (32+B, 24+B).
    position = (BORDER + 32, BORDER + 24)
    assert bare.getpixel(position) != with_vacuum.getpixel(position)
    assert with_vacuum.getpixel(position) == (255, 254, 250, 255)


def test_charger_layer_draws_translucent_dock():
    with_charger = render_image(layers=frozenset({Layer.CHARGER}))
    bare = render_image(layers=frozenset())
    # The charger sits at device (-100, -100) -> grid (2, 2) -> image (16+B, 40+B).
    position = (BORDER + 16, BORDER + 40)
    assert with_charger.getpixel(position) != bare.getpixel(position)


def test_all_layers_change_the_image():
    bare = render_image(layers=frozenset())
    for layer in Layer:
        assert render_image(layers=frozenset({layer})).tobytes() != bare.tobytes(), layer


def test_custom_palette_changes_floor_color():
    image = render_image(palette=Palette(floor=(1, 2, 3)), layers=frozenset())
    assert image.getpixel((BORDER + 20, BORDER + 28)) == (1, 2, 3, 255)


def test_custom_palette_paints_the_border():
    image = render_image(palette=Palette(outside=(9, 9, 9, 255)), layers=frozenset())
    assert image.getpixel((5, 5)) == (9, 9, 9, 255)


def test_scale_one_keeps_native_dimensions():
    image = render_image(scale=1.0, border=0, layers=frozenset())
    assert image.size == (8, 8)
