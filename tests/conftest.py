"""Shared fixtures: an in-process fake vacuum speaking the miIO protocol."""

from __future__ import annotations

import asyncio
import struct

import pytest

from xiaomi_vacuum_sdk.miot.message_codec import HEADER_LENGTH, MAGIC, MessageCodec

TOKEN = "00112233445566778899aabbccddeeff"
DEVICE_ID = bytes.fromhex("075f0e97")
DEVICE_TIMESTAMP = 1_767_323_045


class FakeVacuum(asyncio.DatagramProtocol):
    """UDP server that mimics a MIoT vacuum for one device token."""

    def __init__(self, token: str = TOKEN):
        self.codec = MessageCodec(bytes.fromhex(token))
        self.device_id = DEVICE_ID
        self.timestamp = DEVICE_TIMESTAMP
        self.handlers = {}
        self.received = []
        self.hello_count = 0
        self.drop_hellos = 0
        self.drop_requests = 0
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    @property
    def port(self):
        return self.transport.get_extra_info("sockname")[1]

    def datagram_received(self, data, addr):
        if len(data) == HEADER_LENGTH:
            self.hello_count += 1
            if self.drop_hellos > 0:
                self.drop_hellos -= 1
                return
            hello_reply = (
                struct.pack(">HHI4sI", MAGIC, HEADER_LENGTH, 0, self.device_id, self.timestamp)
                + b"\xff" * 16
            )
            self.transport.sendto(hello_reply, addr)
            return
        payload = self.codec.parse(data).payload
        self.received.append(payload)
        if self.drop_requests > 0:
            self.drop_requests -= 1
            return
        response = self.handlers[payload["method"]](payload)
        if isinstance(response, bytes):
            self.transport.sendto(response, addr)
            return
        self.timestamp += 1
        datagram = self.codec.build_request(
            self.device_id, self.timestamp, {"id": payload["id"], **response}
        )
        self.transport.sendto(datagram, addr)


@pytest.fixture
async def fake_vacuum():
    loop = asyncio.get_running_loop()
    protocol = FakeVacuum()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: protocol, local_addr=("127.0.0.1", 0)
    )
    yield protocol
    transport.close()
