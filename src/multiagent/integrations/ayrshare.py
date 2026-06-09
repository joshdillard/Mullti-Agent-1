"""Ayrshare — unified provider for TikTok + LinkedIn (and more).

One API key (AYRSHARE_API_KEY) replaces the separate TikTok and LinkedIn app
reviews and OAuth flows: Ayrshare handles posting *and* analytics across
TikTok, LinkedIn, Telegram, X, Instagram, etc.

Safety: posting is an outward-facing action, so `post()` defaults to a
dry-run (composes + returns the payload without publishing). Set
AYRSHARE_AUTO_POST=true to actually publish/schedule.

Docs: https://www.ayrshare.com/docs  ·  SDK: pip install social-post-api
Every live call is wrapped so a transient API error degrades to demo data
instead of crashing an agent.
"""

from __future__ import annotations

import os
from typing import Any

import requests

from .base import Integration

API = "https://api.ayrshare.com/api"


class Ayrshare(Integration):
    name = "ayrshare"
    env_vars = ("AYRSHARE_API_KEY",)

    @property
    def auto_post(self) -> bool:
        return os.getenv("AYRSHARE_AUTO_POST", "").lower() in ("1", "true", "yes")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.env('AYRSHARE_API_KEY')}"}

    # --- posting ------------------------------------------------------------
    def post(
        self,
        text: str,
        platforms: list[str],
        *,
        media_urls: list[str] | None = None,
        schedule_date: str | None = None,
    ) -> dict[str, Any]:
        """Publish or schedule a post. Dry-run unless AYRSHARE_AUTO_POST=true."""
        payload: dict[str, Any] = {"post": text, "platforms": platforms}
        if media_urls:
            payload["mediaUrls"] = media_urls
        if schedule_date:
            payload["scheduleDate"] = schedule_date

        if not self.configured:
            self.demo("post")
            return {"status": "demo", "payload": payload}
        if not self.auto_post:
            self.log.info(
                "DRY-RUN Ayrshare post to %s (set AYRSHARE_AUTO_POST=true to publish)",
                platforms,
            )
            return {"status": "dry_run", "payload": payload}
        try:
            r = requests.post(f"{API}/post", json=payload, headers=self._headers(), timeout=60)
            r.raise_for_status()
            return {"status": "ok", "response": r.json()}
        except requests.RequestException as exc:
            self.log.warning("Ayrshare post failed: %s", exc)
            return {"status": "error", "error": str(exc), "payload": payload}

    # --- analytics ----------------------------------------------------------
    def social_analytics(self, platforms: list[str]) -> dict[str, Any]:
        """User-level analytics (followers, views, engagement) per platform."""
        if not self.configured:
            self.demo("social_analytics")
            return {}
        try:
            r = requests.post(
                f"{API}/analytics/social",
                json={"platforms": platforms},
                headers=self._headers(),
                timeout=60,
            )
            r.raise_for_status()
            return r.json()
        except requests.RequestException as exc:
            self.log.warning("Ayrshare analytics failed: %s", exc)
            return {}

    def history(self, platform: str | None = None, limit: int = 25) -> list[dict[str, Any]]:
        """Posts made through Ayrshare, newest first (with engagement when available)."""
        if not self.configured:
            self.demo("history")
            return []
        try:
            params = {"lastRecords": limit}
            if platform:
                params["platform"] = platform
            r = requests.get(f"{API}/history", params=params, headers=self._headers(), timeout=60)
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, list) else data.get("history", [])
        except requests.RequestException as exc:
            self.log.warning("Ayrshare history failed: %s", exc)
            return []
