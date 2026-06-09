"""Zernio — unified social posting + DMs/inbox across 15 platforms.

One API key handles posting (TikTok, LinkedIn, Instagram, X, ...) AND the
inbox: reading and replying to DMs, plus starting new conversations for cold
outreach. This makes it the primary social provider for this stack.

Safety (outward actions never fire by accident):
  - post()          dry-run unless ZERNIO_AUTO_POST=true
  - send_message()  dry-run unless ZERNIO_AUTO_SEND=true  (DMs / cold outreach)

Base URL: https://zernio.com/api   ·   Auth: Authorization: Bearer sk_...
Docs: https://docs.zernio.com
Every live call degrades to demo data / a safe dict on error.
"""

from __future__ import annotations

import os
from typing import Any

import requests

from .base import Integration

API = "https://zernio.com/api/v1"


class Zernio(Integration):
    name = "zernio"
    env_vars = ("ZERNIO_API_KEY",)

    @property
    def auto_post(self) -> bool:
        return os.getenv("ZERNIO_AUTO_POST", "").lower() in ("1", "true", "yes")

    @property
    def auto_send(self) -> bool:
        return os.getenv("ZERNIO_AUTO_SEND", "").lower() in ("1", "true", "yes")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.env('ZERNIO_API_KEY')}"}

    # --- posting ------------------------------------------------------------
    def post(
        self,
        text: str,
        platforms: list[str],
        *,
        media_urls: list[str] | None = None,
        schedule_date: str | None = None,
    ) -> dict[str, Any]:
        """Publish or schedule a post. Dry-run unless ZERNIO_AUTO_POST=true."""
        payload: dict[str, Any] = {"content": text, "platforms": platforms}
        if media_urls:
            payload["media"] = media_urls
        if schedule_date:
            payload["scheduledAt"] = schedule_date

        if not self.configured:
            self.demo("post")
            return {"status": "demo", "payload": payload}
        if not self.auto_post:
            self.log.info("DRY-RUN Zernio post to %s (set ZERNIO_AUTO_POST=true)", platforms)
            return {"status": "dry_run", "payload": payload}
        try:
            r = requests.post(f"{API}/posts", json=payload, headers=self._headers(), timeout=60)
            r.raise_for_status()
            return {"status": "ok", "response": r.json()}
        except requests.RequestException as exc:
            self.log.warning("Zernio post failed: %s", exc)
            return {"status": "error", "error": str(exc), "payload": payload}

    # --- inbox / DMs --------------------------------------------------------
    def unread_conversations(self, limit: int = 25) -> list[dict[str, Any]]:
        """Return recent DM conversations (with the latest inbound message)."""
        if not self.configured:
            self.demo("unread_conversations")
            return _SAMPLE_DMS[:limit]
        try:
            r = requests.get(
                f"{API}/inbox/conversations",
                params={"unread": "true", "limit": limit},
                headers=self._headers(),
                timeout=60,
            )
            r.raise_for_status()
            data = r.json()
            convos = data.get("data", data) if isinstance(data, dict) else data
            return [_map_convo(c) for c in convos] if isinstance(convos, list) else []
        except requests.RequestException as exc:
            self.log.warning("Zernio inbox failed: %s", exc)
            return []

    def send_message(self, conversation_id: str, text: str) -> dict[str, Any]:
        """Reply in a DM thread. Dry-run unless ZERNIO_AUTO_SEND=true."""
        if not self.configured:
            self.demo("send_message")
            return {"status": "demo"}
        if not self.auto_send:
            self.log.info("DRY-RUN Zernio DM to %s (set ZERNIO_AUTO_SEND=true)", conversation_id)
            return {"status": "dry_run", "conversation_id": conversation_id, "text": text}
        try:
            r = requests.post(
                f"{API}/inbox/conversations/{conversation_id}/messages",
                json={"content": text},
                headers=self._headers(),
                timeout=60,
            )
            r.raise_for_status()
            return {"status": "ok", "response": r.json()}
        except requests.RequestException as exc:
            self.log.warning("Zernio send failed: %s", exc)
            return {"status": "error", "error": str(exc)}

    def start_conversation(self, platform: str, recipient: str, text: str) -> dict[str, Any]:
        """Open a new DM thread for cold outreach. Dry-run unless ZERNIO_AUTO_SEND."""
        if not self.configured:
            self.demo("start_conversation")
            return {"status": "demo"}
        if not self.auto_send:
            self.log.info("DRY-RUN Zernio outreach to %s on %s", recipient, platform)
            return {"status": "dry_run", "platform": platform, "recipient": recipient, "text": text}
        try:
            r = requests.post(
                f"{API}/inbox/conversations",
                json={"platform": platform, "recipient": recipient, "content": text},
                headers=self._headers(),
                timeout=60,
            )
            r.raise_for_status()
            return {"status": "ok", "response": r.json()}
        except requests.RequestException as exc:
            self.log.warning("Zernio outreach failed: %s", exc)
            return {"status": "error", "error": str(exc)}


def _map_convo(c: dict[str, Any]) -> dict[str, Any]:
    last = c.get("lastMessage") or c.get("last_message") or {}
    return {
        "id": c.get("id", ""),
        "platform": c.get("platform", "?"),
        "participant": c.get("participant") or c.get("from") or c.get("username", "someone"),
        "last_message": last.get("content", last) if isinstance(last, dict) else last,
        "unread": c.get("unread", True),
    }


_SAMPLE_DMS = [
    {"id": "c1", "platform": "instagram", "participant": "@jenny.makes", "unread": True,
     "last_message": "Do you do brand reels? what are your rates for a monthly package?"},
    {"id": "c2", "platform": "linkedin", "participant": "Marcus Reed", "unread": True,
     "last_message": "Loved your edit breakdown — can we hop on a quick call this week?"},
    {"id": "c3", "platform": "tiktok", "participant": "@foodie.films", "unread": True,
     "last_message": "what mic + lens combo do you use for the kitchen shots??"},
]
