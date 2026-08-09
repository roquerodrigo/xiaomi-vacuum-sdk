"""Root of the map-handling exception hierarchy."""

from __future__ import annotations


class MapError(Exception):
    """Base error for every failure raised by the map context."""
