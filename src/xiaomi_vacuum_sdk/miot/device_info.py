"""Result of the ``miIO.info`` handshake."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..json_types import JsonObject


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    """Device identity reported by ``miIO.info``."""

    model: str
    mac_address: str | None
    firmware_version: str | None
    hardware_version: str | None
    raw: JsonObject

    @classmethod
    def from_payload(cls, payload: JsonObject) -> DeviceInfo:
        """Build from the raw ``miIO.info`` result object."""
        return cls(
            model=str(payload.get("model") or ""),
            mac_address=_optional_string(payload, "mac"),
            firmware_version=_optional_string(payload, "fw_ver"),
            hardware_version=_optional_string(payload, "hw_ver"),
            raw=payload,
        )


def _optional_string(payload: JsonObject, key: str) -> str | None:
    value = payload.get(key)
    return str(value) if value is not None else None
