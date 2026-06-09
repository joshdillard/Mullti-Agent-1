"""Telegram delivery — fully live with just a bot token + chat id."""

from __future__ import annotations

import requests

from .base import Integration


class Telegram(Integration):
    name = "telegram"
    env_vars = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")

    def send(self, text: str) -> bool:
        if not self.configured:
            self.demo("send")
            self.log.info("would send to Telegram:\n%s", text)
            return False
        token = self.env("TELEGRAM_BOT_TOKEN")
        chat_id = self.env("TELEGRAM_CHAT_ID")
        # Telegram caps messages at 4096 chars.
        for chunk in _chunks(text, 4000):
            resp = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": chunk, "disable_web_page_preview": True},
                timeout=30,
            )
            resp.raise_for_status()
        return True


def _chunks(text: str, size: int):
    for i in range(0, len(text), size):
        yield text[i : i + size]
