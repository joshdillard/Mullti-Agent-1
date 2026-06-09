"""Execution context handed to every agent run.

Bundles the shared reasoning layer, settings, lazily-constructed integration
adapters, per-agent state, and the delivery/notify layer so an agent body
reads like plain business logic.
"""

from __future__ import annotations

import logging

from ..integrations import Integrations
from ..llm import LLM
from ..notify import Notifier
from ..settings import Settings
from .state import State


class Context:
    def __init__(
        self, agent_name: str, settings: Settings, params: dict | None = None
    ) -> None:
        self.agent_name = agent_name
        self.settings = settings
        self.config = settings.agent_config(agent_name)
        #: runtime arguments from the CLI (e.g. --topic for a manual agent)
        self.params = params or {}
        self.business = settings.business
        self.log = logging.getLogger(f"multiagent.agent.{agent_name}")

        self.llm = LLM(settings.model)
        self.integrations = Integrations()
        self.notify = Notifier(self.integrations, self.config.get("deliver_to", []))
        self.state = State(settings.state_dir / f"{agent_name}.json")

    # Convenience pass-throughs to the most-used integrations.
    @property
    def tiktok(self):
        return self.integrations.tiktok

    @property
    def linkedin(self):
        return self.integrations.linkedin

    @property
    def gmail(self):
        return self.integrations.gmail

    @property
    def sheets(self):
        return self.integrations.sheets

    @property
    def docs(self):
        return self.integrations.docs

    @property
    def stripe(self):
        return self.integrations.stripe

    @property
    def web(self):
        return self.integrations.web

    @property
    def zernio(self):
        return self.integrations.zernio
