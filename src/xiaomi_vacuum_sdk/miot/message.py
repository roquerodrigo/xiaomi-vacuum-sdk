"""Decoded miIO packet."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..json_types import JsonObject


@dataclass(frozen=True, slots=True)
class Message:
    """One miIO datagram after decryption: header fields plus JSON payload."""

    device_id: bytes
    timestamp: int
    payload: JsonObject | None

    @property
    def is_hello_reply(self) -> bool:
        """True for the 32-byte handshake reply, which carries no payload."""
        return self.payload is None
