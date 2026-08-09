"""MIoT action address."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ActionAddress:
    """Identifies one MIoT action by service id and action id."""

    siid: int
    aiid: int
