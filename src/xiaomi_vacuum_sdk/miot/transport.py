"""Async UDP transport for the miIO protocol."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from .exceptions import ACK_TIMEOUT_CODE, MiotAckTimeoutError, MiotConnectionError, MiotDeviceError
from .message_codec import HELLO_PACKET, MessageCodec

if TYPE_CHECKING:
    from collections.abc import Callable

    from ..json_types import JsonObject, JsonValue
    from .message import Message

    type _MessageFilter = Callable[[Message], bool]

log: logging.Logger = logging.getLogger("xiaomi_vacuum_sdk.miot")

MIIO_PORT = 54321
RECOVERABLE_ERROR_CODES = frozenset({-30001, ACK_TIMEOUT_CODE})
_MAX_REQUEST_ID = 9999
_RETRY_ID_JUMP = 100


class MiotTransport(asyncio.DatagramProtocol):
    """
    Sends miIO requests over a single UDP endpoint and matches their replies.

    Requests are serialized behind a lock: the protocol has no reliable
    correlation for concurrent in-flight commands, and the devices answer one
    command at a time anyway. A handshake (hello packet) resolves the device
    id and clock before the first request and again after any timeout.
    """

    def __init__(
        self, host: str, token: bytes, timeout: float, retry_count: int, port: int = MIIO_PORT
    ) -> None:
        self._host = host
        self._port = port
        self._codec = MessageCodec(token)
        self._timeout = timeout
        self._retry_count = retry_count
        self._lock = asyncio.Lock()
        self._datagrams: asyncio.Queue[bytes | Exception] = asyncio.Queue()
        self._transport: asyncio.DatagramTransport | None = None
        self._handshaken = False
        self._device_id = b"\x00\x00\x00\x00"
        self._device_timestamp = 0
        self._request_id = 0

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Store the datagram transport once the endpoint is up."""
        if isinstance(transport, asyncio.DatagramTransport):
            self._transport = transport

    def connection_lost(self, _exc: Exception | None) -> None:
        """Drop the endpoint so the next request reconnects."""
        self._transport = None
        self._handshaken = False

    def datagram_received(self, data: bytes, _addr: tuple[str | int, ...]) -> None:
        """Queue an incoming datagram for the waiting request."""
        self._datagrams.put_nowait(data)

    def error_received(self, exc: Exception) -> None:
        """Queue a socket-level error (e.g. ICMP port unreachable)."""
        self._datagrams.put_nowait(exc)

    async def request(self, method: str, params: JsonValue) -> JsonValue:
        """
        Send one command and return its ``result``, retrying transient failures.

        Timeouts trigger a fresh handshake and an id jump before the retry;
        recoverable device errors (``-30001`` busy, ``-9999`` ack timeout) are
        retried as-is. When retries run out the last error is raised —
        ``MiotAckTimeoutError`` for an unacked command, ``MiotDeviceError``
        for any other device error, ``MiotConnectionError`` for silence.
        """
        async with self._lock:
            for attempt in range(self._retry_count + 1):
                try:
                    await self._ensure_handshake()
                    return await self._exchange(method, params)
                except MiotConnectionError:
                    self._handshaken = False
                    self._request_id = min(self._request_id + _RETRY_ID_JUMP, _MAX_REQUEST_ID - 1)
                    if attempt == self._retry_count:
                        raise
                except MiotDeviceError as error:
                    if error.code not in RECOVERABLE_ERROR_CODES or attempt == self._retry_count:
                        raise
                log.debug(
                    "Retrying %s against %s (attempt %d/%d)",
                    method,
                    self._host,
                    attempt + 1,
                    self._retry_count,
                )
            raise MiotConnectionError(f"Failed to execute {method}: retries exhausted")

    async def close(self) -> None:
        """Close the UDP endpoint."""
        if self._transport is not None:
            self._transport.close()
            self._transport = None
        self._handshaken = False

    async def _ensure_handshake(self) -> None:
        if self._transport is None:
            loop = asyncio.get_running_loop()
            await loop.create_datagram_endpoint(lambda: self, remote_addr=(self._host, self._port))
        if self._handshaken:
            return
        self._drain_stale_datagrams()
        self._send(HELLO_PACKET)
        message = await self._receive(lambda m: m.is_hello_reply, "handshake")
        self._device_id = message.device_id
        self._device_timestamp = message.timestamp
        self._handshaken = True
        log.debug("Handshake ok: device_id=%s", message.device_id.hex())

    async def _exchange(self, method: str, params: JsonValue) -> JsonValue:
        request_id = self._next_request_id()
        payload: JsonObject = {"id": request_id, "method": method, "params": params}
        self._drain_stale_datagrams()
        self._send(self._codec.build_request(self._device_id, self._device_timestamp + 1, payload))
        message = await self._receive(
            lambda m: m.payload is not None and m.payload.get("id") == request_id, method
        )
        self._device_timestamp = message.timestamp
        reply = message.payload
        if reply is None:
            raise MiotConnectionError(f"Failed to execute {method}: empty reply")
        error = reply.get("error")
        if isinstance(error, dict):
            _raise_device_error(method, error)
        return reply.get("result")

    async def _receive(self, matches: _MessageFilter, method: str) -> Message:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self._timeout
        last_parse_error: MiotConnectionError | None = None
        while True:
            try:
                async with asyncio.timeout_at(deadline):
                    item = await self._datagrams.get()
            except TimeoutError:
                if last_parse_error is not None:
                    raise last_parse_error from None
                raise MiotConnectionError(
                    f"Failed to execute {method}: no response from {self._host} "
                    f"within {self._timeout}s"
                ) from None
            if isinstance(item, Exception):
                raise MiotConnectionError(f"Failed to execute {method}: {item}") from item
            try:
                message = self._codec.parse(item)
            except MiotConnectionError as parse_error:
                last_parse_error = parse_error
                log.debug("Ignoring unparseable datagram: %s", parse_error)
                continue
            if matches(message):
                return message
            log.debug("Ignoring unrelated datagram (%d bytes)", len(item))

    def _send(self, datagram: bytes) -> None:
        if self._transport is None:
            raise MiotConnectionError(f"Failed to send to {self._host}: endpoint is closed")
        self._transport.sendto(datagram)

    def _drain_stale_datagrams(self) -> None:
        while not self._datagrams.empty():
            self._datagrams.get_nowait()

    def _next_request_id(self) -> int:
        self._request_id += 1
        if self._request_id >= _MAX_REQUEST_ID:
            self._request_id = 1
        return self._request_id


def _raise_device_error(method: str, error: dict[str, JsonValue]) -> None:
    code = error.get("code")
    message = str(error.get("message", ""))
    if not isinstance(code, int):
        raise MiotDeviceError(method, 0, message or str(error))
    if code == ACK_TIMEOUT_CODE:
        raise MiotAckTimeoutError(method, message)
    raise MiotDeviceError(method, code, message)
