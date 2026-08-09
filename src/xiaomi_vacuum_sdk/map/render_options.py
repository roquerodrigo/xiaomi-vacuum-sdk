"""Rendering configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

from .layer import Layer
from .palette import Palette

_ALL_LAYERS = frozenset(Layer)


@dataclass(frozen=True, slots=True)
class RenderOptions:
    """
    Controls how a map is drawn; every field has a sensible default.

    ``scale`` multiplies the raw map resolution (device maps are typically
    a few hundred pixels wide). Sizes are in output pixels.
    """

    palette: Palette = field(default_factory=Palette)
    layers: frozenset[Layer] = _ALL_LAYERS
    scale: float = 8.0
    vacuum_radius: int = 18
    path_width: int = 2
    charger_radius: int = 10
