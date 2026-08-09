"""Drawable map layers."""

from __future__ import annotations

from enum import StrEnum, unique


@unique
class Layer(StrEnum):
    """One overlay the renderer can draw on top of the floor image."""

    CHARGER = "charger"
    PATH = "path"
    VACUUM_POSITION = "vacuum_position"
    NO_GO_ZONES = "no_go_zones"
    NO_MOP_ZONES = "no_mop_zones"
    VIRTUAL_WALLS = "virtual_walls"
    ZONES = "zones"
