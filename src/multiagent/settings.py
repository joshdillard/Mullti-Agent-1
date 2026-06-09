"""Process-wide settings, loaded from environment + config/agents.yaml."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Project root = two levels up from this file (src/multiagent/settings.py).
ROOT = Path(__file__).resolve().parents[2]

# Load .env once at import time. Real env vars always win over the file.
load_dotenv(ROOT / ".env")

DEFAULT_MODEL = "claude-opus-4-8"


@dataclass(frozen=True)
class Business:
    """Context about the business, injected into every agent's prompt."""

    name: str = os.getenv("BUSINESS_NAME", "Your Studio")
    niche: str = os.getenv("BUSINESS_NICHE", "video production and AI content")
    handle: str = os.getenv("BUSINESS_HANDLE", "@yourhandle")

    def as_prompt(self) -> str:
        return (
            f"Business name: {self.name}\n"
            f"Niche: {self.niche}\n"
            f"Primary social handle: {self.handle}"
        )


@dataclass
class Settings:
    model: str = os.getenv("MULTIAGENT_MODEL", DEFAULT_MODEL)
    timezone: str = "America/New_York"
    business: Business = field(default_factory=Business)
    agents: dict[str, dict[str, Any]] = field(default_factory=dict)
    state_dir: Path = ROOT / "state"

    @classmethod
    def load(cls, config_path: Path | None = None) -> "Settings":
        path = config_path or (ROOT / "config" / "agents.yaml")
        data: dict[str, Any] = {}
        if path.exists():
            data = yaml.safe_load(path.read_text()) or {}
        s = cls(
            timezone=data.get("timezone", "America/New_York"),
            agents=data.get("agents", {}),
        )
        s.state_dir.mkdir(parents=True, exist_ok=True)
        return s

    def agent_config(self, name: str) -> dict[str, Any]:
        return self.agents.get(name, {}) or {}
