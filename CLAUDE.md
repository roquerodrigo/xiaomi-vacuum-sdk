# xiaomi-vacuum-sdk

Async Python SDK for **Xiaomi MIoT robot vacuums**, built as the single
replacement for `python-miio` and `vacuum-map-parser-xiaomi` in the
`ha-xiaomi-vacuum` Home Assistant integration. Two bounded contexts:

- **`miot/`** — local control over the encrypted MIoT UDP protocol
  (port 54321): handshake, AES-128-CBC payload cipher, `miIO.info`,
  `get_properties`, `set_properties`, `action`. Async-native (asyncio
  datagram transport), no executor needed. No legacy miIO support
  (`get_prop`, device classes, discovery, CLI, cloud).
- **`map/`** — cloud map blob to PNG: AES-CBC decrypt (key derived from
  model + device id, including the `xiaomi.` → `mi.` model-key quirk),
  optional `{"data": "<base64>"}` envelope unwrap, zlib inflate, JSON
  payload parse into typed `MapData`, PIL render to PNG bytes. Rendering is
  CPU-bound and sync — consumers wrap it in an executor.

Supported devices are whatever the consumer maps: the SDK is model-agnostic
and takes property/action addresses as input. Reference models are the
X20 Max (`xiaomi.vacuum.d109gl`) and S20+ (`xiaomi.vacuum.b108gl`).

## Always read `CODE_STYLE.md` first

Before creating, renaming or restructuring any file/class/function, **read
[`CODE_STYLE.md`](./CODE_STYLE.md)**. It is the single source of truth for
conventions: language, file organisation, naming, typing, imports,
docstrings, comments, logging, error messages, public API surface,
conventional commits, packaging, testing, lint workflow.

## Verification workflow

After every code change, always run lint then tests, in that order, before
declaring the task done:

```bash
uv run ruff format . && uv run ruff check . --fix && uv run mypy src
uv run pytest
```

Both gates mirror CI. Skip this only when the change literally cannot
affect lint or tests (e.g., README-only edits).

## Downstream consumer

This package is published to PyPI and consumed by the `ha-xiaomi-vacuum`
Home Assistant integration (sibling repo), which pins an **exact** version
(`xiaomi-vacuum-sdk==X.Y.Z`) in both its `pyproject.toml` and
`custom_components/xiaomi_vacuum/manifest.json`. A new release here does
not reach the integration until that pin is bumped there.

Runtime dependencies stay floor-only (`>=`, never `==`, never an upper
bound): Home Assistant pins its own transitive dependencies exactly, and a
cap here would conflict the moment HA moves first. `cryptography` and
`pillow` are both shipped by HA core, so the SDK adds no real install cost
inside HA.

## Testing

The suite is fully offline: the datagram transport is faked at the asyncio
boundary, packet tests use golden vectors captured from the real devices,
and map tests use golden encrypted blobs inlined in `tests/map_fixtures.py`.
Live validation against real vacuums happens via
`examples/`, which read host/token from `.env` (never committed).
