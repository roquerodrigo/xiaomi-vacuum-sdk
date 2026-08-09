"""MIoT property address."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PropertyAddress:
    """Identifies one MIoT property by service id and property id."""

    siid: int
    piid: int
