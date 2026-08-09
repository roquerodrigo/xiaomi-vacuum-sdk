"""Exception hierarchy for the map context."""

from __future__ import annotations

from .base import MapError
from .decrypt import MapDecryptError
from .parse import MapParseError

__all__ = ["MapDecryptError", "MapError", "MapParseError"]
