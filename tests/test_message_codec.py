"""Golden-vector tests: the codec must match python-miio's packet bytes exactly."""

from __future__ import annotations

import pytest

from xiaomi_vacuum_sdk.miot.exceptions import MiotConnectionError
from xiaomi_vacuum_sdk.miot.message_codec import HELLO_PACKET, MessageCodec

TOKEN = bytes.fromhex("00112233445566778899aabbccddeeff")
DEVICE_ID = bytes.fromhex("075f0e97")
TIMESTAMP = 1_767_323_045

GOLDEN_REQUEST = bytes.fromhex(
    "2131008000000000075f0e97695735a5c9f53f4ee3e8d5e16afe9b42eb55e8b9"
    "679569e4e919cfa5b1eb0d3aef4aff9f2b1f6843dd55e5d923d7862fa906dafa"
    "d219853df4181d4d7730597b936fd7eab4cc9802efd5eb5bf07e188f37c70034"
    "e0506a615a1c31c9681dd3cc7ef167ddd59e49a52e4263bfaa1c28484bc2bed1"
)
GOLDEN_REQUEST_PAYLOAD = {
    "id": 42,
    "method": "get_properties",
    "params": [{"did": "status", "siid": 2, "piid": 1}],
}
GOLDEN_REPLY = bytes.fromhex(
    "2131009000000000075f0e97695735a540f0a5e803b9d1d263b75e8fb2e7abce"
    "2c66a65a0b948d4571cc5228497fe73753fa4d5081fcd1d169c6a93201f2df6b"
    "453654b577124c82f90492e11181b607ef6ffe60790fcab978b497bbf1fd94fe"
    "4e4e7f50746cc2811f3e081cc534bcafe53ba42823adb9e16b947d6cf9912d1f"
    "12c303aaac33643db8c8d62aecce5800"
)
GOLDEN_REPLY_PAYLOAD = {
    "id": 42,
    "result": [{"did": "status", "siid": 2, "piid": 1, "code": 0, "value": 7}],
    "exe_time": 100,
}


def test_build_request_matches_python_miio_bytes():
    codec = MessageCodec(TOKEN)
    built = codec.build_request(DEVICE_ID, TIMESTAMP, GOLDEN_REQUEST_PAYLOAD)
    assert built == GOLDEN_REQUEST


def test_parse_reply_built_by_python_miio():
    codec = MessageCodec(TOKEN)
    message = codec.parse(GOLDEN_REPLY)
    assert message.device_id == DEVICE_ID
    assert message.timestamp == TIMESTAMP
    assert message.payload == GOLDEN_REPLY_PAYLOAD


def test_roundtrip():
    codec = MessageCodec(TOKEN)
    built = codec.build_request(DEVICE_ID, TIMESTAMP, GOLDEN_REQUEST_PAYLOAD)
    message = codec.parse(built)
    assert message.payload == GOLDEN_REQUEST_PAYLOAD
    assert not message.is_hello_reply


def test_hello_packet_is_the_documented_magic_bytes():
    assert HELLO_PACKET.hex() == "21310020" + "ff" * 28


def test_parse_hello_reply_has_no_payload():
    codec = MessageCodec(TOKEN)
    hello_reply = bytes.fromhex("21310020") + bytes(4) + DEVICE_ID + bytes(4) + b"\xff" * 16
    message = codec.parse(hello_reply)
    assert message.is_hello_reply
    assert message.device_id == DEVICE_ID


def test_parse_rejects_wrong_token_checksum():
    codec = MessageCodec(bytes.fromhex("ff112233445566778899aabbccddeeff"))
    with pytest.raises(MiotConnectionError, match="token"):
        codec.parse(GOLDEN_REPLY)


def test_parse_rejects_short_packet():
    codec = MessageCodec(TOKEN)
    with pytest.raises(MiotConnectionError, match="too short"):
        codec.parse(b"\x21\x31")


def test_parse_rejects_bad_magic():
    codec = MessageCodec(TOKEN)
    with pytest.raises(MiotConnectionError, match="magic"):
        codec.parse(b"\x00" * 32)


def test_parse_rejects_length_mismatch():
    codec = MessageCodec(TOKEN)
    with pytest.raises(MiotConnectionError, match="length"):
        codec.parse(GOLDEN_REPLY[:-1])
