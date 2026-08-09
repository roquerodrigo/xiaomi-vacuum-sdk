# xiaomi-vacuum-sdk

Async Python SDK for Xiaomi MIoT robot vacuums: local control over the
encrypted MIoT UDP protocol, and rendering of the cloud map blob to PNG.

Built as a focused replacement for `python-miio` + `vacuum-map-parser-xiaomi`
covering exactly the surface a vacuum integration needs — no legacy miIO
protocol, no CLI, no device discovery. Reference models are the Xiaomi Robot
Vacuum X20 Max (`xiaomi.vacuum.d109gl`) and S20+ (`xiaomi.vacuum.b108gl`);
the API is model-agnostic and takes MIoT property/action addresses as input.

## Install

```bash
pip install xiaomi-vacuum-sdk
```

Requires Python >= 3.13. Runtime dependencies: `cryptography`, `pillow`.

## Local control

```python
from xiaomi_vacuum_sdk import ActionAddress, MiotClient, PropertyAddress

client = MiotClient(host="192.168.1.50", token="ffffffffffffffffffffffffffffffff")
try:
    info = await client.info()
    print(info.model, info.firmware_version)

    state = await client.get_properties(
        {
            "status": PropertyAddress(siid=2, piid=1),
            "battery_level": PropertyAddress(siid=3, piid=1),
        }
    )
    print(state)

    await client.call_action(ActionAddress(siid=2, aiid=1))
    await client.set_property(PropertyAddress(siid=7, piid=4), 1)
finally:
    await client.close()
```

All calls are async-native (asyncio UDP transport, no threads). Errors form
a typed hierarchy rooted at `MiotError`:

- `MiotConnectionError` — network failure or response timeout.
- `MiotDeviceError` — the device answered with a non-zero error code
  (`code`, `message` attributes).
- `MiotAckTimeoutError` — the device accepted the command but never sent
  the ack (Xiaomi vacuums do this routinely while busy); a distinct type so
  callers can choose optimistic handling.

## Map rendering

```python
from xiaomi_vacuum_sdk import MapRenderer, RenderOptions

renderer = MapRenderer(RenderOptions())
png = renderer.render(blob, model="xiaomi.vacuum.d109gl", device_id="412345678")
```

`blob` is the encrypted map exactly as downloaded from the Xiaomi cloud
(`get_file_url` object storage). The renderer absorbs the format quirks —
model-derived AES key, optional `{"data": "<base64>"}` envelope, zlib
inflate — and returns finished PNG bytes. Rendering is CPU-bound and sync;
wrap it in an executor inside async applications.

`RenderOptions` controls palette, room colors, drawn layers, scale and
element sizes; every field has a sensible default.

## License

MIT.
