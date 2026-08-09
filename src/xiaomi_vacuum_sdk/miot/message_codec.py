"""Binary codec for miIO packets."""

from __future__ import annotations

import hashlib
import json
import struct
from typing import TYPE_CHECKING, cast

from .exceptions import MiotConnectionError
from .message import Message
from .payload_cipher import PayloadCipher

if TYPE_CHECKING:
    from ..json_types import JsonObject

MAGIC = 0x2131
HEADER_LENGTH = 32
HELLO_PACKET = bytes.fromhex("21310020" + "ff" * 28)


class MessageCodec:
    """
    Builds and parses miIO datagrams for one device token.

    Packet layout: magic (2) | length (2) | unknown (4) | device id (4) |
    timestamp (4) | MD5 checksum (16) | AES-encrypted JSON payload. The
    checksum covers the first 16 header bytes, the token and the encrypted
    payload. The 32-byte hello reply carries no payload and no verifiable
    checksum (the field echoes handshake material instead).
    """

    def __init__(self, token: bytes) -> None:
        self._token = token
        self._cipher = PayloadCipher(token)

    def build_request(self, device_id: bytes, timestamp: int, payload: JsonObject) -> bytes:
        """Encode one request datagram addressed to the device."""
        data = self._cipher.encrypt(json.dumps(payload).encode())
        header = struct.pack(">HHI4sI", MAGIC, HEADER_LENGTH + len(data), 0, device_id, timestamp)
        checksum = _md5(header + self._token + data)
        return header + checksum + data

    def parse(self, datagram: bytes) -> Message:
        """Decode one datagram from the device, verifying its checksum."""
        if len(datagram) < HEADER_LENGTH:
            raise MiotConnectionError(f"Failed to parse packet: {len(datagram)} bytes is too short")
        magic, length, _unknown, device_id, timestamp = struct.unpack(">HHI4sI", datagram[:16])
        if magic != MAGIC:
            raise MiotConnectionError(f"Failed to parse packet: bad magic 0x{magic:04x}")
        if length != len(datagram):
            raise MiotConnectionError(
                f"Failed to parse packet: length field {length} != {len(datagram)} bytes"
            )
        if length == HEADER_LENGTH:
            return Message(device_id=device_id, timestamp=timestamp, payload=None)
        checksum = datagram[16:32]
        data = datagram[32:]
        if _md5(datagram[:16] + self._token + data) != checksum:
            raise MiotConnectionError(
                "Failed to verify packet checksum: the device token is likely wrong"
            )
        return Message(device_id=device_id, timestamp=timestamp, payload=self._decode_payload(data))

    def _decode_payload(self, data: bytes) -> JsonObject:
        try:
            decoded = json.loads(self._cipher.decrypt(data))
        except ValueError as error:
            raise MiotConnectionError(f"Failed to decode packet payload: {error}") from error
        if not isinstance(decoded, dict):
            raise MiotConnectionError("Failed to decode packet payload: not a JSON object")
        return cast("JsonObject", decoded)


def _md5(data: bytes) -> bytes:
    return hashlib.md5(data, usedforsecurity=False).digest()
