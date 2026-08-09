"""High-level async client for one MIoT device."""

from __future__ import annotations

from itertools import batched
from typing import TYPE_CHECKING

from .device_info import DeviceInfo
from .exceptions import MiotConnectionError, MiotDeviceError
from .transport import MIIO_PORT, MiotTransport

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from ..json_types import JsonValue
    from .action_address import ActionAddress
    from .property_address import PropertyAddress

type PropertyValue = bool | float | int | str | None
"""Scalar value of one MIoT property; ``None`` when the device reported an error."""

TOKEN_HEX_LENGTH = 32
DEFAULT_TIMEOUT = 10.0
DEFAULT_RETRY_COUNT = 3
DEFAULT_MAX_PROPERTIES_PER_REQUEST = 15


class MiotClient:
    """
    Async client for the encrypted MIoT UDP protocol (``miIO`` port 54321).

    Commands: ``miIO.info``, ``get_properties``, ``set_properties`` and
    ``action`` — the surface a MIoT vacuum needs. The client is
    model-agnostic; callers provide property/action addresses.
    """

    def __init__(
        self,
        host: str,
        token: str,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        retry_count: int = DEFAULT_RETRY_COUNT,
        port: int = MIIO_PORT,
    ) -> None:
        try:
            token_bytes = bytes.fromhex(token)
        except ValueError as error:
            raise ValueError(
                f"Failed to parse token: expected {TOKEN_HEX_LENGTH} hexadecimal characters"
            ) from error
        if len(token) != TOKEN_HEX_LENGTH:
            raise ValueError(
                f"Failed to parse token: expected {TOKEN_HEX_LENGTH} hexadecimal characters"
            )
        self._transport = MiotTransport(host, token_bytes, timeout, retry_count, port)

    async def info(self) -> DeviceInfo:
        """Read the device identity (``miIO.info`` handshake)."""
        result = await self._transport.request("miIO.info", [])
        if not isinstance(result, dict):
            raise MiotConnectionError("Failed to read device info: unexpected reply shape")
        return DeviceInfo.from_payload(result)

    async def get_properties(
        self,
        mapping: Mapping[str, PropertyAddress],
        *,
        max_per_request: int = DEFAULT_MAX_PROPERTIES_PER_REQUEST,
    ) -> dict[str, PropertyValue]:
        """
        Read every mapped property, returning values keyed by mapping name.

        Properties the device answered with a non-zero code — or did not
        answer at all — come back as ``None``. Requests are chunked because
        the devices cap how many properties one command may carry.
        """
        values: dict[str, PropertyValue] = dict.fromkeys(mapping)
        requests: list[JsonValue] = [
            {"did": name, "siid": address.siid, "piid": address.piid}
            for name, address in mapping.items()
        ]
        for chunk in batched(requests, max_per_request, strict=False):
            result = await self._transport.request("get_properties", list(chunk))
            if not isinstance(result, list):
                raise MiotConnectionError("Failed to read properties: unexpected reply shape")
            for row in result:
                if not isinstance(row, dict):
                    continue
                name = row.get("did")
                if not isinstance(name, str) or name not in values or row.get("code") != 0:
                    continue
                value = row.get("value")
                if isinstance(value, bool | float | int | str):
                    values[name] = value
        return values

    async def set_property(self, address: PropertyAddress, value: bool | int | str) -> None:
        """Write one property, raising ``MiotDeviceError`` if the device rejects it."""
        result = await self._transport.request(
            "set_properties",
            [
                {
                    "did": f"set-{address.siid}-{address.piid}",
                    "siid": address.siid,
                    "piid": address.piid,
                    "value": value,
                }
            ],
        )
        if not isinstance(result, list):
            return
        for row in result:
            if not isinstance(row, dict):
                continue
            code = row.get("code")
            if isinstance(code, int) and code != 0:
                raise MiotDeviceError(
                    "set_properties",
                    code,
                    f"property {address.siid}/{address.piid} rejected",
                )

    async def call_action(
        self, address: ActionAddress, params: Sequence[JsonValue] | None = None
    ) -> JsonValue:
        """
        Invoke one action, raising ``MiotDeviceError`` if the device rejects it.

        ``params`` follows the MIoT ``in`` shape: a list of
        ``{"piid": ..., "value": ...}`` objects (or raw values for actions
        that take a bare payload).
        """
        result = await self._transport.request(
            "action",
            {
                "did": f"call-{address.siid}-{address.aiid}",
                "siid": address.siid,
                "aiid": address.aiid,
                "in": list(params) if params is not None else [],
            },
        )
        if isinstance(result, dict):
            code = result.get("code")
            if isinstance(code, int) and code != 0:
                raise MiotDeviceError(
                    "action", code, f"action {address.siid}/{address.aiid} rejected"
                )
        return result

    async def close(self) -> None:
        """Close the underlying UDP endpoint."""
        await self._transport.close()
