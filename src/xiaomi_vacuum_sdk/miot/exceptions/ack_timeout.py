"""The device accepted a command but never sent the ack."""

from __future__ import annotations

from .device import MiotDeviceError

ACK_TIMEOUT_CODE = -9999


class MiotAckTimeoutError(MiotDeviceError):
    """
    The device answered ``-9999 user ack timeout`` after every retry.

    Xiaomi vacuums routinely accept an action (start / pause / room-sweep) and
    then never ack because the robot is already busy moving. The command
    usually *did* reach the device, so callers may choose to treat this as
    accepted and reconcile state on their next poll.
    """

    def __init__(self, method: str, message: str) -> None:
        super().__init__(method, ACK_TIMEOUT_CODE, message)
