"""Root of the local-control exception hierarchy."""

from __future__ import annotations


class MiotError(Exception):
    """Base error for every failure raised by the MIoT local-control context."""
