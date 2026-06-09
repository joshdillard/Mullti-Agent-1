"""Shared base for integration adapters.

Each adapter declares the env vars it needs. If they're all present it runs
live; otherwise `configured` is False and the adapter returns representative
demo data (clearly logged), so the whole system is runnable before any keys
are wired up.
"""

from __future__ import annotations

import logging
import os


class Integration:
    name: str = "base"
    env_vars: tuple[str, ...] = ()

    def __init__(self) -> None:
        self.log = logging.getLogger(f"multiagent.integration.{self.name}")
        self.configured = bool(self.env_vars) and all(
            os.getenv(v) for v in self.env_vars
        )
        if not self.configured:
            self.log.debug("%s not configured — running in demo mode", self.name)

    def env(self, key: str, default: str | None = None) -> str | None:
        return os.getenv(key, default)

    def demo(self, what: str) -> None:
        """Log that demo data is being returned in place of a live call."""
        missing = [v for v in self.env_vars if not os.getenv(v)]
        self.log.info(
            "DEMO %s.%s — returning sample data (set %s to go live)",
            self.name,
            what,
            ", ".join(missing) or "credentials",
        )
