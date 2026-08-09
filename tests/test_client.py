"""End-to-end client tests against the in-process fake vacuum."""

from __future__ import annotations

import pytest

from xiaomi_vacuum_sdk import (
    ActionAddress,
    MiotAckTimeoutError,
    MiotClient,
    MiotConnectionError,
    MiotDeviceError,
    PropertyAddress,
)

TOKEN = "00112233445566778899aabbccddeeff"
INFO_RESULT = {
    "model": "xiaomi.vacuum.d109gl",
    "mac": "AA:BB:CC:DD:EE:FF",
    "fw_ver": "1.0.4",
    "hw_ver": "Linux",
    "token": "redacted",
}


def make_client(fake_vacuum, **overrides):
    options = {"timeout": 0.3, "retry_count": 2, "port": fake_vacuum.port}
    options.update(overrides)
    return MiotClient("127.0.0.1", TOKEN, **options)


async def test_info_returns_device_identity(fake_vacuum):
    fake_vacuum.handlers["miIO.info"] = lambda payload: {"result": INFO_RESULT}
    client = make_client(fake_vacuum)
    try:
        info = await client.info()
    finally:
        await client.close()
    assert info.model == "xiaomi.vacuum.d109gl"
    assert info.mac_address == "AA:BB:CC:DD:EE:FF"
    assert info.firmware_version == "1.0.4"
    assert info.hardware_version == "Linux"
    assert info.raw == INFO_RESULT


async def test_get_properties_maps_values_by_name(fake_vacuum):
    def answer(payload):
        # Real vacuums echo their own device id in `did`, not the request's
        # marker — rows must resolve by siid/piid alone.
        rows = []
        for request in payload["params"]:
            row = {**request, "did": "1154085352"}
            if request["did"] == "battery_level":
                rows.append({**row, "code": -4004})
            elif request["did"] == "fan_speed":
                continue
            else:
                rows.append({**row, "code": 0, "value": 7})
        return {"result": rows}

    fake_vacuum.handlers["get_properties"] = answer
    client = make_client(fake_vacuum)
    try:
        values = await client.get_properties(
            {
                "status": PropertyAddress(siid=2, piid=1),
                "battery_level": PropertyAddress(siid=3, piid=1),
                "fan_speed": PropertyAddress(siid=7, piid=1),
            }
        )
    finally:
        await client.close()
    assert values == {"status": 7, "battery_level": None, "fan_speed": None}


async def test_get_properties_chunks_large_mappings(fake_vacuum):
    fake_vacuum.handlers["get_properties"] = lambda payload: {
        "result": [{**request, "code": 0, "value": 1} for request in payload["params"]]
    }
    mapping = {f"property_{index}": PropertyAddress(siid=2, piid=index) for index in range(20)}
    client = make_client(fake_vacuum)
    try:
        values = await client.get_properties(mapping)
    finally:
        await client.close()
    assert all(value == 1 for value in values.values())
    chunk_sizes = [len(payload["params"]) for payload in fake_vacuum.received]
    assert chunk_sizes == [15, 5]


async def test_set_property_sends_miot_shape(fake_vacuum):
    fake_vacuum.handlers["set_properties"] = lambda payload: {
        "result": [{"did": payload["params"][0]["did"], "code": 0}]
    }
    client = make_client(fake_vacuum)
    try:
        await client.set_property(PropertyAddress(siid=7, piid=4), 1)
    finally:
        await client.close()
    sent = fake_vacuum.received[0]["params"][0]
    assert sent == {"did": "set-7-4", "siid": 7, "piid": 4, "value": 1}


async def test_set_property_rejection_raises_device_error(fake_vacuum):
    fake_vacuum.handlers["set_properties"] = lambda payload: {
        "result": [{"did": "set-7-4", "code": -4003}]
    }
    client = make_client(fake_vacuum)
    try:
        with pytest.raises(MiotDeviceError) as excinfo:
            await client.set_property(PropertyAddress(siid=7, piid=4), 99)
    finally:
        await client.close()
    assert excinfo.value.code == -4003


async def test_call_action_sends_miot_shape_and_returns_result(fake_vacuum):
    fake_vacuum.handlers["action"] = lambda payload: {"result": {"code": 0, "out": []}}
    client = make_client(fake_vacuum)
    try:
        result = await client.call_action(
            ActionAddress(siid=4, aiid=1), params=[{"piid": 1, "value": "12,14"}]
        )
    finally:
        await client.close()
    assert result == {"code": 0, "out": []}
    sent = fake_vacuum.received[0]["params"]
    assert sent == {
        "did": "call-4-1",
        "siid": 4,
        "aiid": 1,
        "in": [{"piid": 1, "value": "12,14"}],
    }


async def test_call_action_without_params_sends_empty_in(fake_vacuum):
    fake_vacuum.handlers["action"] = lambda payload: {"result": {"code": 0}}
    client = make_client(fake_vacuum)
    try:
        await client.call_action(ActionAddress(siid=2, aiid=1))
    finally:
        await client.close()
    assert fake_vacuum.received[0]["params"]["in"] == []


async def test_call_action_result_code_rejection_raises(fake_vacuum):
    fake_vacuum.handlers["action"] = lambda payload: {"result": {"code": -4004}}
    client = make_client(fake_vacuum)
    try:
        with pytest.raises(MiotDeviceError) as excinfo:
            await client.call_action(ActionAddress(siid=2, aiid=1))
    finally:
        await client.close()
    assert excinfo.value.code == -4004


async def test_ack_timeout_retries_then_raises_distinct_error(fake_vacuum):
    fake_vacuum.handlers["action"] = lambda payload: {
        "error": {"code": -9999, "message": "user ack timeout"}
    }
    client = make_client(fake_vacuum)
    try:
        with pytest.raises(MiotAckTimeoutError):
            await client.call_action(ActionAddress(siid=2, aiid=1))
    finally:
        await client.close()
    assert len(fake_vacuum.received) == 3


async def test_recoverable_error_retries_then_succeeds(fake_vacuum):
    answers = [
        {"error": {"code": -30001, "message": "device busy"}},
        {"result": {"code": 0}},
    ]
    fake_vacuum.handlers["action"] = lambda payload: answers.pop(0)
    client = make_client(fake_vacuum)
    try:
        await client.call_action(ActionAddress(siid=2, aiid=1))
    finally:
        await client.close()
    assert len(fake_vacuum.received) == 2


async def test_non_recoverable_error_raises_immediately(fake_vacuum):
    fake_vacuum.handlers["action"] = lambda payload: {
        "error": {"code": -4004, "message": "unsupported"}
    }
    client = make_client(fake_vacuum)
    try:
        with pytest.raises(MiotDeviceError) as excinfo:
            await client.call_action(ActionAddress(siid=2, aiid=1))
    finally:
        await client.close()
    assert excinfo.value.code == -4004
    assert len(fake_vacuum.received) == 1


async def test_dropped_request_triggers_rehandshake_and_retry(fake_vacuum):
    fake_vacuum.handlers["miIO.info"] = lambda payload: {"result": INFO_RESULT}
    fake_vacuum.drop_requests = 1
    client = make_client(fake_vacuum)
    try:
        info = await client.info()
    finally:
        await client.close()
    assert info.model == "xiaomi.vacuum.d109gl"
    assert fake_vacuum.hello_count == 2


async def test_unreachable_device_raises_connection_error(fake_vacuum):
    fake_vacuum.drop_hellos = 10
    fake_vacuum.drop_requests = 10
    client = make_client(fake_vacuum, timeout=0.1)
    try:
        with pytest.raises(MiotConnectionError):
            await client.info()
    finally:
        await client.close()


async def test_garbage_reply_surfaces_parse_error(fake_vacuum):
    fake_vacuum.handlers["miIO.info"] = lambda payload: b"\x00" * 40
    client = make_client(fake_vacuum, timeout=0.1, retry_count=0)
    try:
        with pytest.raises(MiotConnectionError, match="magic"):
            await client.info()
    finally:
        await client.close()


async def test_client_reconnects_after_close(fake_vacuum):
    fake_vacuum.handlers["miIO.info"] = lambda payload: {"result": INFO_RESULT}
    client = make_client(fake_vacuum)
    try:
        await client.info()
        await client.close()
        info = await client.info()
    finally:
        await client.close()
    assert info.model == "xiaomi.vacuum.d109gl"


def test_rejects_non_hexadecimal_token():
    with pytest.raises(ValueError, match="hexadecimal"):
        MiotClient("127.0.0.1", "zz" * 16)


def test_rejects_wrong_length_token():
    with pytest.raises(ValueError, match="32"):
        MiotClient("127.0.0.1", "0011223344")
