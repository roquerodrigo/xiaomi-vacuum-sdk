"""Network-level failure talking to the device."""

from __future__ import annotations

from .base import MiotError


class MiotConnectionError(MiotError):
    """The device could not be reached or did not answer in time."""
