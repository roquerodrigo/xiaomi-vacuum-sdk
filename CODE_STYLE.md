# Code Style Guide

Style conventions for the `xiaomi-vacuum-sdk` Python SDK. Run
`uv run ruff format . && uv run ruff check . --fix && uv run mypy src` before
committing — all three must exit cleanly. `uv run pytest` follows.

**Always read this file before adding or restructuring code.**

## Language

- Code is written in **English**: file names, class names, function names,
  variable names, dictionary keys, identifier strings.
- The conversation language with the user can be Portuguese or anything else;
  what is committed to disk stays English.

## File organization

- **Source layout is `src/xiaomi_vacuum_sdk/`.** Tests in `tests/`, packaging
  in `pyproject.toml`. Hatchling is the build backend.
- **One top-level class per file.** Multiple semantically related classes get
  grouped into a package directory with one class per submodule and an
  `__init__.py` re-exporting the public symbols.
  - Example: `miot/` contains `client.py`, `transport.py`, `message_codec.py`,
    plus `__init__.py`.
  - Example: `map/` contains `renderer.py`, `blob_decryptor.py`,
    `map_payload_parser.py`, plus `__init__.py`.
- **Public surface goes through the package `__init__.py`.** Anything not
  re-exported there is internal — prefix with `_` if intended to stay private.
- **TypedDicts and `type` aliases do not count as "classes"** for this rule —
  they live alongside related code.
- **Helper functions** may live in the same file as the single class that
  uses them. Module-level private helpers are prefixed `_`.

## Naming

- Public classes are `CapWords`: `MiotClient`, `DeviceInfo`, `MapRenderer`,
  `RenderOptions`.
- Exception classes end with `Error`: `MiotError`, `MiotConnectionError`,
  `MiotDeviceError`, `MapParseError`.
- Module names are `snake_case`. Subpackages are organized by concern
  (`miot`, `map`).
- Private attributes / functions are prefixed with `_`.

## Typing

**Strict typing. No `Any`, no bare collection generics.** Mypy enforces this.

Banned: `typing.Any`, `object` as a value type, bare `dict` / `list` /
`tuple` / `set`, `dict[str, Any]`.

Required:

- `@dataclass(frozen=True, slots=True)` for structured records
  (`DeviceInfo`, `PropertyAddress`, `ActionAddress`, …).
- `enum.Enum` subclasses for fixed sets of values (`Layer`).
- Named `type` aliases for shared shapes (`JsonObject`, `JsonValue`,
  `PropertyValue`).
- Always type return values explicitly. Never rely on type inference for
  public APIs.
- Type-hinted module-level loggers:
  `log: logging.Logger = logging.getLogger(...)`.

The SDK ships a `py.typed` marker so downstream consumers get type info.

## Imports

- Always start every module with `from __future__ import annotations` so type
  hints become lazy strings.
- Same-package relative imports (`from .module import …`) are the default.
- Move type-only imports into a `TYPE_CHECKING` block:

  ```python
  from __future__ import annotations
  from typing import TYPE_CHECKING

  if TYPE_CHECKING:
      from collections.abc import Mapping
      from .device_info import DeviceInfo
  ```

- `noqa` comments require a written justification inline. Never silence to
  "make ruff happy" — fix the underlying code.

## Docstrings

- Every public class, function, method (including `@property`) has a docstring.
- A single sentence is usually enough. Describe the *contract* or the *why*,
  not the obvious implementation.
- Module-level docstring at the top of every `.py` file.
- Avoid restating the type — the signature already does that.

## Comments

- Default to **no comments**. Add one only when the *why* is not obvious from
  the code: a hidden constraint, a workaround, a subtle invariant, a protocol
  reference (e.g. "IV is fixed by the map format, not derived").
- Never describe *what* the code does — well-named identifiers handle that.
- **No section dividers** like `# --- helpers ---` to group related
  declarations. If a file has so many sections that you feel the need for
  visual separators, split it into multiple files instead.

## Logging

- Module-level logger:
  `log: logging.Logger = logging.getLogger("xiaomi_vacuum_sdk.<area>")` (e.g.
  `"xiaomi_vacuum_sdk.miot"`, `"xiaomi_vacuum_sdk.map"`). Don't use
  `__name__` directly — the explicit dotted name lets users scope log levels
  precisely.
- Use **lazy `%`-formatting**, never f-strings:

  ```python
  log.debug("Handshake ok: device_id=%s", device_id)   # ✓
  log.debug(f"Handshake ok: token={token}")            # ✗ leaks the token
  ```

- Levels:
  - `debug` — packet sizes, handshake steps, truncated payloads.
  - `info` — nothing by default; the SDK is a library, stay quiet.
  - `warning` — recoverable failures (retry, fallback path).
  - `error` / `exception` — unrecoverable. `exception` inside `except` blocks
    captures the traceback.
- Never log the device token, derived AES keys, or full decrypted payloads at
  levels above `debug`.

## Error messages

- Format: `"Failed to <verb> <object>: <cause>"`. Keep them short and
  grep-able.
- Custom exceptions form two hierarchies, one per context. `MiotError` is the
  root for local control: `MiotConnectionError` (socket timeout / network
  failure) and `MiotDeviceError` (the device answered with a non-zero code,
  carrying `code` and `message`), with the narrower `MiotAckTimeoutError`
  (code `-9999`, the device accepted the command but never acked). `MapError`
  is the root for map handling: `MapDecryptError` and `MapParseError`. Wrap
  raw `OSError` / `zlib` / `json` errors at the boundary so callers only
  catch these hierarchies.
- Pre-validate inputs before opening a socket so user-facing errors point at
  the bad input, not a downstream traceback.

## Public API surface

- Anything imported in the package `__init__.py` is the public contract.
  Renaming or removing those symbols is a `BREAKING CHANGE:`.
- Internal modules can change shape freely as long as the public re-exports
  keep working.

## Conventional commits

All commits follow [Conventional Commits](https://www.conventionalcommits.org/),
in **English**:

| Type | Meaning | Bump |
|---|---|---|
| `feat` | New feature | minor |
| `fix` | Bug fix | patch |
| `perf` | Performance improvement | patch |
| `deps` | Dependency bump | patch |
| `docs` | Documentation only | none |
| `refactor` | Refactor without behavior change | none |
| `test` | Test-only change | none |
| `ci` | CI / tooling change | none |
| `chore` | Anything else (rarely) | none |

- Subject line: imperative mood, lowercase, no trailing period.
- Use scopes when useful: `feat(miot): add property read batching`.
- A `BREAKING CHANGE:` footer (or `!` after type) bumps the major version.

## Packaging

- Build backend: `hatchling`. Wheel and sdist contain `src/xiaomi_vacuum_sdk`.
- `requires-python = ">=3.13"`. Don't bump this without a `BREAKING CHANGE:`
  footer.
- Public dependencies: keep them minimal and use `>=` lower bounds, not pins.
  Currently `cryptography>=44.0` (AES-CBC) and `pillow>=11.0` (map render).
- The `[dependency-groups] dev` group carries test-only deps;
  `[dependency-groups] lint` carries ruff + mypy.
- A `py.typed` marker ships in the wheel so consumers see type info.

## Testing

- Tests live in `tests/`. `uv run pytest` runs the suite. Aim for high
  coverage on the codec/cipher/parser layers since they're the byte-level
  surface most likely to regress silently.
- The suite is fully offline — the datagram transport is faked at the asyncio
  boundary, and unit tests use byte-level fixtures captured from the real
  devices. Live exercising against a real vacuum happens through the scripts
  in `examples/`, which read host/token from `.env` (never committed).

## Linting and verification

- Ruff configuration in `pyproject.toml` under `[tool.ruff]`.
- Mypy configuration in `pyproject.toml` under `[tool.mypy]` (strict).
- After every change run the three-step lint pipeline + `pytest`. Both
  gates mirror CI:

  ```bash
  uv run ruff format . && uv run ruff check . --fix && uv run mypy src
  uv run pytest
  ```
