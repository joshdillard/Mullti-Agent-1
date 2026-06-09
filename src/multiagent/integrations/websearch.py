"""Web research adapter.

Defaults to Claude's built-in web_search tool (no extra key) via the LLM
layer, so brand-mention / competitor / trend agents have real web reach.
This adapter mostly signals availability; agents call ctx.llm.complete(...,
web_search=True) for the actual searching.
"""

from __future__ import annotations

from .base import Integration


class Web(Integration):
    name = "web"
    env_vars = ()  # built-in via Claude web_search; always "available"

    def __init__(self) -> None:
        super().__init__()
        # Web research is available whenever the LLM has an API key.
        self.configured = True
