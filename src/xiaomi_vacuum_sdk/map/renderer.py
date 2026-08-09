"""Rendering of a parsed map to a PNG image."""

from __future__ import annotations

import io
import math
from itertools import pairwise
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw

from .blob_decryptor import BlobDecryptor
from .coordinate_system import CoordinateSystem
from .layer import Layer
from .map_point import MapPoint
from .payload_parser import MapPayloadParser
from .render_options import RenderOptions

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from PIL.Image import Image as PilImage
    from PIL.ImageDraw import ImageDraw as PilDraw

    from .map_data import MapData
    from .palette import Color, Palette
    from .quadrilateral import Quadrilateral

_PIXEL_FLOOR_VALUES = frozenset({1, 2})
_PIXEL_ROOM_MINIMUM = 3
_PIXEL_ROOM_MAXIMUM = 63
_ROOM_NUMBER_OFFSET = 7
_VACUUM_DETAIL_MINIMUM_RADIUS = 8
_PATH_END_CAP_MINIMUM_WIDTH = 4
_MINIMUM_PATH_POINTS = 2
_RGB_CHANNELS = 3


class MapRenderer:
    """
    Renders the encrypted cloud map blob straight to PNG bytes.

    Rendering is CPU-bound and synchronous — wrap calls in an executor
    inside async applications. The drawing pipeline reproduces the
    reference parser pixel-for-pixel with the default options.
    """

    def __init__(self, options: RenderOptions | None = None) -> None:
        self._options = options if options is not None else RenderOptions()
        self._decryptor = BlobDecryptor()
        self._parser = MapPayloadParser()

    def render(self, blob: bytes, *, model: str, device_id: str) -> bytes:
        """Decrypt, parse and draw one map blob, returning finished PNG bytes."""
        map_data = self._parser.parse(self._decryptor.decrypt(blob, model, device_id))
        image = self._draw(map_data)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def _draw(self, map_data: MapData) -> PilImage:
        options = self._options
        image = _floor_image(map_data, options.palette)
        if options.scale != 1:
            image = image.resize(
                (int(map_data.width * options.scale), int(map_data.height * options.scale)),
                resample=Image.Resampling.NEAREST,
            )
        if options.border > 0:
            image = _add_border(image, options.border, options.palette)
        coordinates = CoordinateSystem.for_map(map_data, options.scale, options.border)
        if Layer.CHARGER in options.layers and map_data.charger is not None:
            image = _draw_charger(image, map_data.charger, coordinates, options)
        if Layer.PATH in options.layers:
            image = _draw_path(image, map_data.path, coordinates, options)
        if Layer.VACUUM_POSITION in options.layers and map_data.vacuum is not None:
            image = _draw_vacuum(image, map_data.vacuum, coordinates, options)
        if Layer.NO_GO_ZONES in options.layers:
            image = _draw_zones(
                image,
                map_data.no_go_zones,
                coordinates,
                options.palette.no_go_zone,
                options.palette.no_go_zone_outline,
            )
        if Layer.NO_MOP_ZONES in options.layers:
            image = _draw_zones(
                image,
                map_data.no_mop_zones,
                coordinates,
                options.palette.no_mop_zone,
                options.palette.no_mop_zone_outline,
            )
        if Layer.VIRTUAL_WALLS in options.layers:
            image = _draw_virtual_walls(image, map_data, coordinates, options.palette)
        if Layer.ZONES in options.layers:
            image = _draw_zones(
                image,
                map_data.zones,
                coordinates,
                options.palette.zone,
                options.palette.zone_outline,
            )
        return image


def _floor_image(map_data: MapData, palette: Palette) -> PilImage:
    outside = _rgba(palette.outside)
    floor = _rgba(palette.floor)
    wall = _rgba(palette.wall)
    color_cache: dict[int, bytes] = {}
    rows = bytearray()
    for grid_row in reversed(range(map_data.height)):
        row_start = grid_row * map_data.width
        for value in map_data.pixels[row_start : row_start + map_data.width]:
            cached = color_cache.get(value)
            if cached is None:
                if value == 0:
                    cached = outside
                elif value in _PIXEL_FLOOR_VALUES:
                    cached = floor
                elif _PIXEL_ROOM_MINIMUM <= value <= _PIXEL_ROOM_MAXIMUM:
                    cached = _rgba(palette.room_color(value + _ROOM_NUMBER_OFFSET))
                else:
                    cached = wall
                color_cache[value] = cached
            rows += cached
    return Image.frombytes("RGBA", (map_data.width, map_data.height), bytes(rows))


def _add_border(image: PilImage, border: int, palette: Palette) -> PilImage:
    width, height = image.size
    canvas = Image.new(
        "RGBA", (width + border * 2, height + border * 2), tuple(_rgba(palette.outside))
    )
    canvas.alpha_composite(image, (border, border))
    return canvas


def _draw_charger(
    image: PilImage,
    charger: MapPoint,
    coordinates: CoordinateSystem,
    options: RenderOptions,
) -> PilImage:
    x, y = coordinates.to_image(charger)
    radius = options.charger_radius
    angle = -(charger.angle if charger.angle is not None else 0)
    fill = options.palette.charger
    outline = options.palette.charger_outline

    def draw_function(draw: PilDraw) -> None:
        draw.pieslice(
            ((x - radius, y - radius), (x + radius, y + radius)),
            angle + 90,
            angle - 90,
            outline=outline,
            fill=fill,
        )

    return _draw_on_layer(image, draw_function, (fill, outline))


def _draw_path(
    image: PilImage,
    path: Sequence[MapPoint],
    coordinates: CoordinateSystem,
    options: RenderOptions,
) -> PilImage:
    if len(path) < _MINIMUM_PATH_POINTS:
        return image
    color = options.palette.path
    width = options.path_width
    points = [coordinates.to_image(point) for point in path]

    def draw_function(draw: PilDraw) -> None:
        end_cap = None
        for (start_x, start_y), (end_x, end_y) in pairwise(points):
            draw.line((start_x, start_y, end_x, end_y), width=width, fill=color)
            if width > _PATH_END_CAP_MINIMUM_WIDTH:
                radius = width / 2
                if end_cap is None:
                    end_cap = (
                        (start_x - radius, start_y - radius),
                        (start_x + radius, start_y + radius),
                    )
                    draw.pieslice(end_cap, 0, 360, outline=color, fill=color)
                end_cap = ((end_x - radius, end_y - radius), (end_x + radius, end_y + radius))
                draw.pieslice(end_cap, 0, 360, outline=color, fill=color)

    return _draw_on_layer(image, draw_function, (color,))


def _draw_vacuum(
    image: PilImage,
    vacuum: MapPoint,
    coordinates: CoordinateSystem,
    options: RenderOptions,
) -> PilImage:
    x, y = coordinates.to_image(vacuum)
    heading = vacuum.angle if vacuum.angle is not None else 0
    radius = options.vacuum_radius
    fill = options.palette.vacuum
    outline = options.palette.vacuum_outline
    sixteenth = radius / 16

    def draw_function(draw: PilDraw) -> None:
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline=outline, fill=fill)
        if radius >= _VACUUM_DETAIL_MINIMUM_RADIUS:
            secondary = sixteenth * 14
            draw.ellipse(
                (x - secondary, y - secondary, x + secondary, y + secondary), outline=outline
            )
        cover_start = (heading + 104) / 180 * math.pi
        cover_end = (heading - 104) / 180 * math.pi
        cover_radius = sixteenth * 13
        draw.line(
            (
                x - cover_radius * math.cos(cover_start),
                y + cover_radius * math.sin(cover_start),
                x - cover_radius * math.cos(cover_end),
                y + cover_radius * math.sin(cover_end),
            ),
            width=1,
            fill=outline,
        )
        heading_radians = heading / 180 * math.pi
        lidar_x = x + sixteenth * 3 * math.cos(heading_radians)
        lidar_y = y - sixteenth * 3 * math.sin(heading_radians)
        lidar_radius = sixteenth * 4
        draw.ellipse(
            (
                lidar_x - lidar_radius,
                lidar_y - lidar_radius,
                lidar_x + lidar_radius,
                lidar_y + lidar_radius,
            ),
            outline=outline,
            fill=fill,
        )
        button_color = (
            (outline[0] + fill[0]) // 2,
            (outline[1] + fill[1]) // 2,
            (outline[2] + fill[2]) // 2,
        )
        button_x = x + sixteenth * 10 * math.cos(heading_radians)
        button_y = y - sixteenth * 10 * math.sin(heading_radians)
        button_radius = sixteenth * 2
        draw.ellipse(
            (
                button_x - button_radius,
                button_y - button_radius,
                button_x + button_radius,
                button_y + button_radius,
            ),
            outline=button_color,
            fill=button_color,
        )

    return _draw_on_layer(image, draw_function, (fill, outline))


def _draw_zones(
    image: PilImage,
    zones: Sequence[Quadrilateral],
    coordinates: CoordinateSystem,
    fill: Color,
    outline: Color,
) -> PilImage:
    for zone in zones:
        polygon: list[float] = []
        for corner in zone.corners():
            polygon.extend(coordinates.to_image(corner))

        def draw_function(draw: PilDraw, polygon: list[float] = polygon) -> None:
            draw.polygon(polygon, fill, outline)

        image = _draw_on_layer(image, draw_function, (fill, outline))
    return image


def _draw_virtual_walls(
    image: PilImage,
    map_data: MapData,
    coordinates: CoordinateSystem,
    palette: Palette,
) -> PilImage:
    if not map_data.virtual_walls:
        return image
    color = palette.virtual_wall

    def draw_function(draw: PilDraw) -> None:
        for wall in map_data.virtual_walls:
            start = coordinates.to_image(MapPoint(wall.start_x, wall.start_y))
            end = coordinates.to_image(MapPoint(wall.end_x, wall.end_y))
            draw.line((*start, *end), fill=color, width=2)

    return _draw_on_layer(image, draw_function, (color,))


def _draw_on_layer(
    image: PilImage,
    draw_function: Callable[[PilDraw], None],
    colors: tuple[Color, ...],
) -> PilImage:
    if any(len(color) > _RGB_CHANNELS for color in colors):
        layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
        draw_function(ImageDraw.Draw(layer, "RGBA"))
        return Image.alpha_composite(image, layer)
    draw_function(ImageDraw.Draw(image, "RGBA"))
    return image


def _rgba(color: Color) -> bytes:
    if len(color) == _RGB_CHANNELS:
        return bytes((*color, 255))
    return bytes(color)
