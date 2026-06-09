"""Phyllo — deep creator/audience analytics across TikTok, LinkedIn, etc.

Read-only: Phyllo pulls follower demographics, engagement, and audience data
that go deeper than Ayrshare's. When configured, it becomes the preferred
source for `research_audience` and `weekly_performance_review` demographics.

Auth is HTTP Basic (client id : secret). You connect an account through
Phyllo once and reference it by PHYLLO_ACCOUNT_ID.

Docs: https://docs.getphyllo.com
Every live call degrades to {} on error so agents fall back cleanly to demo.
"""

from __future__ import annotations

import os
from typing import Any

import requests

from .base import Integration

_BASES = {
    "sandbox": "https://api.sandbox.getphyllo.com",
    "staging": "https://api.staging.getphyllo.com",
    "production": "https://api.getphyllo.com",
}


class Phyllo(Integration):
    name = "phyllo"
    env_vars = ("PHYLLO_CLIENT_ID", "PHYLLO_SECRET")

    @property
    def base(self) -> str:
        return _BASES.get(os.getenv("PHYLLO_ENV", "sandbox").lower(), _BASES["sandbox"])

    def _auth(self) -> tuple[str, str]:
        return (self.env("PHYLLO_CLIENT_ID", ""), self.env("PHYLLO_SECRET", ""))

    def audience(self, account_id: str | None = None) -> dict[str, Any]:
        """Return mapped audience demographics for the connected account."""
        account_id = account_id or os.getenv("PHYLLO_ACCOUNT_ID")
        if not self.configured or not account_id:
            self.demo("audience")
            return {}
        try:
            r = requests.get(
                f"{self.base}/v1/audience",
                params={"account_id": account_id},
                auth=self._auth(),
                timeout=60,
            )
            r.raise_for_status()
            return _map_audience(r.json())
        except requests.RequestException as exc:
            self.log.warning("Phyllo audience failed: %s", exc)
            return {}


def _map_audience(data: dict[str, Any]) -> dict[str, Any]:
    """Map Phyllo's audience payload to our internal audience shape."""
    # Phyllo returns demographics under various keys depending on platform; pull
    # what we can and leave the rest blank rather than guessing.
    countries = data.get("countries") or data.get("audience_countries") or []
    gender_age = data.get("gender_age_distribution") or data.get("gender_ages") or []
    return {
        "followers": data.get("follower_count", data.get("followers", 0)),
        "growth_30d": data.get("follower_count_change", "n/a"),
        "top_locations": [c.get("name", c) if isinstance(c, dict) else c for c in countries][:3],
        "age_skew": _top_age(gender_age),
        "gender_skew": _gender_split(gender_age),
        "active_hours": data.get("active_hours", "n/a"),
        "top_themes": [],
        "_source": "phyllo",
    }


def _top_age(gender_age: list) -> str:
    if not gender_age:
        return "n/a"
    top = max(gender_age, key=lambda x: x.get("value", 0) if isinstance(x, dict) else 0)
    return top.get("age_range", "n/a") if isinstance(top, dict) else "n/a"


def _gender_split(gender_age: list) -> str:
    male = sum(x.get("value", 0) for x in gender_age if isinstance(x, dict) and x.get("gender") == "MALE")
    female = sum(x.get("value", 0) for x in gender_age if isinstance(x, dict) and x.get("gender") == "FEMALE")
    total = male + female
    if not total:
        return "n/a"
    return f"{round(male / total * 100)}% male / {round(female / total * 100)}% female"
