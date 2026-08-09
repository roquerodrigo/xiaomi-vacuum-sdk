"""Failure interpreting the decrypted map payload."""

from __future__ import annotations

from .base import MapError


class MapParseError(MapError):
    """The decrypted map payload does not contain a drawable map."""
