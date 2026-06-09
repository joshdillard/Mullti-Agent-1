"""Central execution path shared by the scheduler, CLI, and dashboard.

Builds a context, runs the agent, delivers the result to its channels, and
records the run in history. One place so behavior is identical everywhere.
"""

from __future__ import annotations

from .context import Context
from .history import History, now_iso
from .registry import load_all
from ..settings import Settings


def run_agent(name: str, settings: Settings, params: dict | None = None, *, deliver: bool = True):
    """Run a single agent by name and return its AgentResult."""
    registry = load_all()
    if name not in registry:
        raise KeyError(f"unknown agent '{name}'")

    ctx = Context(name, settings, params=params)
    started = now_iso()
    result = registry[name]().execute(ctx)
    # Tag the result so history knows which agent produced it.
    result.agent_name = name  # type: ignore[attr-defined]

    if deliver:
        ctx.notify.send(result)

    finished = now_iso()
    History(settings.state_dir / "history.json").record(
        result, started_at=started, finished_at=finished
    )
    return result
