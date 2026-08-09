"""Colors used to render the map."""

from __future__ import annotations

from dataclasses import dataclass, field

type Color = tuple[int, int, int] | tuple[int, int, int, int]
"""RGB or RGBA color, channels 0-255."""

_DEFAULT_ROOM_COLORS: tuple[Color, ...] = (
    (214, 196, 168),
    (180, 198, 210),
    (196, 202, 164),
    (204, 192, 210),
    (220, 204, 170),
    (186, 210, 206),
    (212, 194, 196),
    (190, 200, 216),
    (200, 190, 174),
    (186, 210, 206),
    (214, 196, 168),
    (196, 202, 164),
    (204, 192, 210),
    (220, 204, 170),
    (180, 198, 210),
    (212, 194, 196),
    (190, 200, 216),
    (200, 190, 174),
    (186, 210, 206),
    (196, 202, 164),
    (214, 196, 168),
    (204, 192, 210),
    (220, 204, 170),
    (180, 198, 210),
    (212, 194, 196),
    (200, 190, 174),
    (196, 202, 164),
    (186, 210, 206),
    (214, 196, 168),
    (204, 192, 210),
    (220, 204, 170),
    (180, 198, 210),
)


@dataclass(frozen=True, slots=True)
class Palette:
    """Every color the renderer draws with; defaults form a muted green theme."""

    outside: Color = (250, 249, 246, 0)
    floor: Color = (92, 110, 84)
    wall: Color = (92, 110, 84)
    path: Color = (92, 110, 84)
    charger: Color = (45, 74, 43, 220)
    charger_outline: Color = (20, 34, 20)
    vacuum: Color = (255, 254, 250)
    vacuum_outline: Color = (20, 34, 20)
    virtual_wall: Color = (161, 68, 68)
    no_go_zone: Color = (161, 68, 68, 127)
    no_go_zone_outline: Color = (161, 68, 68)
    no_mop_zone: Color = (90, 117, 149, 127)
    no_mop_zone_outline: Color = (90, 117, 149)
    zone: Color = (164, 172, 134, 100)
    zone_outline: Color = (45, 74, 43)
    room_colors: tuple[Color, ...] = field(default=_DEFAULT_ROOM_COLORS)

    def room_color(self, room_number: int) -> Color:
        """
        Color for one room, cycling through ``room_colors``.

        Room numbers beyond the palette wrap around one-based, matching the
        reference parser so existing maps keep their exact colors.
        """
        if room_number > len(self.room_colors):
            room_number = (room_number - 1) % len(self.room_colors) + 1
        return self.room_colors[room_number - 1]
