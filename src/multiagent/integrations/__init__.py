"""Lazily-constructed container for all integration adapters."""

from __future__ import annotations

from .gdocs import Docs
from .gmail import Gmail
from .gsheets import Sheets
from .linkedin import LinkedIn
from .stripe_client import Stripe
from .telegram import Telegram
from .tiktok import TikTok
from .websearch import Web


class Integrations:
    """Holds one instance of each adapter, built on first access."""

    def __init__(self) -> None:
        self._cache: dict[str, object] = {}

    def _get(self, key: str, cls):
        if key not in self._cache:
            self._cache[key] = cls()
        return self._cache[key]

    @property
    def tiktok(self) -> TikTok:
        return self._get("tiktok", TikTok)

    @property
    def linkedin(self) -> LinkedIn:
        return self._get("linkedin", LinkedIn)

    @property
    def gmail(self) -> Gmail:
        return self._get("gmail", Gmail)

    @property
    def sheets(self) -> Sheets:
        return self._get("sheets", Sheets)

    @property
    def docs(self) -> Docs:
        return self._get("docs", Docs)

    @property
    def stripe(self) -> Stripe:
        return self._get("stripe", Stripe)

    @property
    def telegram(self) -> Telegram:
        return self._get("telegram", Telegram)

    @property
    def web(self) -> Web:
        return self._get("web", Web)

    def status(self) -> dict[str, bool]:
        """Which integrations are configured (live) vs demo."""
        return {
            "tiktok": self.tiktok.configured,
            "linkedin": self.linkedin.configured,
            "gmail": self.gmail.configured,
            "sheets": self.sheets.configured,
            "docs": self.docs.configured,
            "stripe": self.stripe.configured,
            "telegram": self.telegram.configured,
            "web": self.web.configured,
        }


__all__ = [
    "Integrations",
    "Docs",
    "Gmail",
    "Sheets",
    "LinkedIn",
    "Stripe",
    "Telegram",
    "TikTok",
    "Web",
]
