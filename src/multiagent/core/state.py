"""Tiny JSON-file key/value store.

Lets agents remember things between runs without a database — e.g. which
content ideas were already suggested, the last revenue snapshot, or which
leads have already been emailed. One file per agent under state/.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class State:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, Any] = {}
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text())
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._flush()

    def append(self, key: str, value: Any, *, cap: int | None = None) -> None:
        items = list(self._data.get(key, []))
        items.append(value)
        if cap is not None:
            items = items[-cap:]
        self._data[key] = items
        self._flush()

    def _flush(self) -> None:
        # Atomic write: a concurrent reader/writer never sees a half-written file.
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._data, indent=2, default=str))
        os.replace(tmp, self.path)
