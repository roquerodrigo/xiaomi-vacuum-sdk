"""Shared JSON type aliases used across the SDK."""

from __future__ import annotations

type JsonValue = str | int | float | bool | list[JsonValue] | dict[str, JsonValue] | None
"""Any value representable in JSON (recursive)."""

type JsonObject = dict[str, JsonValue]
"""A JSON object — string keys to JSON values."""
