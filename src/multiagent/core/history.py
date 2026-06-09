"""Run-history store — what the dashboard reads.

Every agent run appends a record here so you can monitor activity at a glance:
when it ran, whether it succeeded, what it produced, and where it went.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CAP = 300


class History:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._records: list[dict[str, Any]] = []
        if self.path.exists():
            try:
                self._records = json.loads(self.path.read_text())
            except (json.JSONDecodeError, OSError):
                self._records = []

    def record(self, result, *, started_at: str, finished_at: str) -> None:
        body = result.body or ""
        self._records.append(
            {
                "agent": getattr(result, "agent_name", None),
                "title": result.title,
                "ok": result.ok,
                "error": result.error,
                "delivered_to": result.delivered_to,
                "preview": body[:400],
                "body": body[:8000],
                "started_at": started_at,
                "finished_at": finished_at,
            }
        )
        self._records = self._records[-CAP:]
        self.path.write_text(json.dumps(self._records, indent=2, default=str))

    def all(self) -> list[dict[str, Any]]:
        return list(reversed(self._records))  # newest first

    def latest_per_agent(self) -> dict[str, dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for rec in self._records:  # oldest→newest, so last wins
            if rec.get("agent"):
                latest[rec["agent"]] = rec
        return latest


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
