"""Error answered by the device itself."""

from __future__ import annotations

from .base import MiotError


class MiotDeviceError(MiotError):
    """The device answered a command with a non-zero error code."""

    def __init__(self, method: str, code: int, message: str) -> None:
        super().__init__(
            f"Failed to execute {method}: device answered code={code} message={message!r}"
        )
        self.method = method
        self.code = code
        self.message = message
