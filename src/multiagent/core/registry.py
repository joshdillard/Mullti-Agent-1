"""Agent registry + auto-discovery.

Agents register themselves via the @register decorator. `load_all()` imports
every module in multiagent.agents so the decorators fire.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .agent import Agent

REGISTRY: dict[str, type["Agent"]] = {}


def register(cls: type["Agent"]) -> type["Agent"]:
    if not getattr(cls, "name", None):
        raise ValueError(f"{cls.__name__} must define a `name`")
    if cls.name in REGISTRY:
        raise ValueError(f"duplicate agent name: {cls.name}")
    REGISTRY[cls.name] = cls
    return cls


def load_all() -> dict[str, type["Agent"]]:
    """Import every agent module so the registry is fully populated."""
    from .. import agents as agents_pkg

    for mod in pkgutil.iter_modules(agents_pkg.__path__):
        if not mod.name.startswith("_"):
            importlib.import_module(f"{agents_pkg.__name__}.{mod.name}")
    return REGISTRY
