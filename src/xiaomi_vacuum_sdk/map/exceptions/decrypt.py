"""Failure decrypting or inflating the raw map blob."""

from __future__ import annotations

from .base import MapError


class MapDecryptError(MapError):
    """The map blob could not be decrypted or decompressed."""
