"""TikTok adapter — trends, your own post analytics, and audience.

Live mode calls the TikTok Display / Research APIs with TIKTOK_ACCESS_TOKEN.
Those APIs require app review + scopes; until then this returns realistic
sample data so downstream agents produce meaningful output.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .base import Integration


class TikTok(Integration):
    name = "tiktok"
    env_vars = ("TIKTOK_ACCESS_TOKEN",)

    def trending(self, keywords: list[str] | None = None, limit: int = 10) -> list[dict[str, Any]]:
        """Return trending sounds/hashtags/formats relevant to the niche."""
        if not self.configured:
            self.demo("trending")
            return _SAMPLE_TRENDS[:limit]
        # Live: query the TikTok Research API `/v2/research/video/query/`
        # filtered to the niche keywords, aggregate by hashtag/sound.
        raise NotImplementedError(
            "Wire TikTok Research API here using TIKTOK_ACCESS_TOKEN."
        )

    def my_recent_posts(self, days: int = 7) -> list[dict[str, Any]]:
        """Return the user's recent posts with engagement metrics."""
        if not self.configured:
            self.demo("my_recent_posts")
            return _sample_posts(days)
        # Live: GET /v2/video/list/ then /v2/video/query/ for metrics.
        raise NotImplementedError("Wire TikTok Display API video.list here.")

    def audience(self) -> dict[str, Any]:
        """Return follower demographics + top-performing content themes."""
        if not self.configured:
            self.demo("audience")
            return _SAMPLE_AUDIENCE
        # Live: GET /v2/user/info/ + creator insights.
        raise NotImplementedError("Wire TikTok creator insights here.")


_SAMPLE_TRENDS = [
    {"type": "format", "name": "'POV: the client approves on the first cut'", "growth": "+340%"},
    {"type": "sound", "name": "lofi transition whoosh", "uses": 128000, "growth": "+210%"},
    {"type": "hashtag", "name": "#bts_edit", "views": "48M", "growth": "+88%"},
    {"type": "format", "name": "before/after color grade splitscreen", "growth": "+150%"},
    {"type": "hashtag", "name": "#aivideo", "views": "120M", "growth": "+260%"},
    {"type": "format", "name": "'3 settings I changed' quick-tip carousel", "growth": "+95%"},
]


def _sample_posts(days: int) -> list[dict[str, Any]]:
    today = date.today()
    base = [
        ("Behind the scenes of a brand shoot", 42000, 5800, 410, 230),
        ("How I color grade in 60 seconds", 188000, 24000, 1900, 1400),
        ("3 lighting mistakes beginners make", 73000, 9100, 620, 540),
        ("Client reaction to the final cut", 31000, 3300, 180, 95),
        ("AI b-roll: worth it or not?", 251000, 39000, 3100, 2600),
    ]
    return [
        {
            "posted": str(today - timedelta(days=i)),
            "caption": cap,
            "views": v,
            "likes": l,
            "comments": c,
            "shares": s,
        }
        for i, (cap, v, l, c, s) in enumerate(base)
    ]


_SAMPLE_AUDIENCE = {
    "followers": 18400,
    "growth_30d": "+1,250",
    "top_locations": ["United States", "United Kingdom", "Canada"],
    "age_skew": "25-34 (46%)",
    "gender_skew": "58% male / 40% female",
    "active_hours": "7-9pm ET",
    "top_themes": [
        {"theme": "fast editing tutorials", "avg_views": 142000},
        {"theme": "gear/setup reveals", "avg_views": 88000},
        {"theme": "AI workflow tips", "avg_views": 205000},
    ],
}
