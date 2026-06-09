"""Claude-powered reasoning layer.

Thin wrapper around the Anthropic SDK that every agent shares. Defaults to
claude-opus-4-8 with adaptive thinking, and streams responses so large
deliverables (research series, newsletters) never hit request timeouts.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Callable

from .settings import DEFAULT_MODEL

log = logging.getLogger("multiagent.llm")


class LLM:
    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("MULTIAGENT_MODEL", DEFAULT_MODEL)
        self._client = None  # lazy — lets the package import without a key
        #: optional callback fired with each text delta as it streams; the
        #: dashboard sets this to surface live output while an agent runs.
        self.on_text: Callable[[str], None] | None = None

    @property
    def client(self):
        if self._client is None:
            import anthropic  # imported lazily so tests/demo don't require it

            self._client = anthropic.Anthropic()
        return self._client

    def _run(self, kwargs: dict[str, Any], on_text: Callable[[str], None] | None):
        """Stream a request, firing the text callback per delta, and return
        the assembled final message."""
        cb = on_text or self.on_text
        with self.client.messages.stream(**kwargs) as stream:
            if cb is not None:
                for delta in stream.text_stream:
                    try:
                        cb(delta)
                    except Exception:  # noqa: BLE001 - a bad sink must not break a run
                        pass
            return stream.get_final_message()

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 8000,
        effort: str = "high",
        thinking: bool = True,
        web_search: bool = False,
        on_text: Callable[[str], None] | None = None,
    ) -> str:
        """Return the model's text response.

        Streams under the hood and assembles the final message, which keeps
        long generations safely under the SDK's HTTP timeout.
        """
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "output_config": {"effort": effort},
        }
        if system:
            kwargs["system"] = system
        if thinking:
            kwargs["thinking"] = {"type": "adaptive"}
        if web_search:
            kwargs["tools"] = [{"type": "web_search_20260209", "name": "web_search"}]

        message = self._run(kwargs, on_text)
        return "".join(b.text for b in message.content if b.type == "text").strip()

    def complete_json(
        self,
        prompt: str,
        schema: dict[str, Any],
        *,
        system: str | None = None,
        max_tokens: int = 8000,
        effort: str = "high",
        on_text: Callable[[str], None] | None = None,
    ) -> Any:
        """Return a JSON value constrained to `schema` (a JSON Schema dict)."""
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "thinking": {"type": "adaptive"},
            "output_config": {
                "effort": effort,
                "format": {"type": "json_schema", "schema": schema},
            },
        }
        if system:
            kwargs["system"] = system

        message = self._run(kwargs, on_text)
        text = next((b.text for b in message.content if b.type == "text"), "{}")
        return json.loads(text)
