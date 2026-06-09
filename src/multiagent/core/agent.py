"""Base class for every automation agent."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from .context import Context


@dataclass
class AgentResult:
    """What an agent produced on a run."""

    title: str
    body: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    delivered_to: list[str] = field(default_factory=list)
    ok: bool = True
    error: str | None = None

    def summary(self) -> str:
        status = "OK" if self.ok else f"ERROR: {self.error}"
        dests = ", ".join(self.delivered_to) or "—"
        return f"[{status}] {self.title}  (delivered: {dests})"


class Agent:
    #: unique key, also used in config/agents.yaml and the CLI
    name: str = "agent"
    #: one-line human description (mirrors the dashboard card)
    description: str = ""

    def run(self, ctx: Context) -> AgentResult:  # pragma: no cover - interface
        raise NotImplementedError

    # --- runner plumbing ----------------------------------------------------
    def execute(self, ctx: Context) -> AgentResult:
        log = logging.getLogger(f"multiagent.agent.{self.name}")
        start = time.monotonic()
        log.info("running")
        try:
            result = self.run(ctx)
        except Exception as exc:  # noqa: BLE001 - surface, don't crash the scheduler
            log.exception("failed")
            result = AgentResult(
                title=self.description or self.name, ok=False, error=str(exc)
            )
        took = time.monotonic() - start
        log.info("done in %.1fs — %s", took, result.summary())
        return result
