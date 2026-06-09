"""TikTok adapter — trends, your own post analytics, and audience.

Live mode calls the TikTok Display / Research APIs with TIKTOK_ACCESS_TOKEN.
Those APIs require app review + scopes; until then this returns realistic
sample data so downstream agents produce meaningful output.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .ayrshare import Ayrshare
from .base import Integration


class TikTok(Integration):
    name = "tiktok"
    env_vars = ("TIKTOK_ACCESS_TOKEN",)

    def __init__(self) -> None:
        super().__init__()
        # Ayrshare is the recommended provider — it covers TikTok analytics
        # without the official app-review gauntlet. We're "live" if either the
        # direct TikTok token OR an Ayrshare key is present.
        self.ayrshare = Ayrshare()
        self.configured = self.configured or self.ayrshare.configured

    def trending(self, keywords: list[str] | None = None, limit: int = 10) -> list[dict[str, Any]]:
        """Return trending sounds/hashtags/formats relevant to the niche.

        Note: neither Ayrshare nor the official APIs expose a trending feed.
        Trend discovery is handled by the agents via Claude's web_search
        (see spot_viral_opportunities). This returns curated sample trends.
        """
        self.demo("trending")
        return _SAMPLE_TRENDS[:limit]

    def my_recent_posts(self, days: int = 7) -> list[dict[str, Any]]:
        """Return the user's recent posts with engagement metrics."""
        if self.ayrshare.configured:
            posts = _from_ayrshare_history(self.ayrshare.history(platform="tiktok"))
            if posts:
                return posts
        self.demo("my_recent_posts")
        return _sample_posts(days)

    def audience(self) -> dict[str, Any]:
        """Return follower demographics + top-performing content themes."""
        if self.ayrshare.configured:
            data = self.ayrshare.social_analytics(["tiktok"])
            mapped = _from_ayrshare_analytics(data)
            if mapped:
                return mapped
        self.demo("audience")
        return _SAMPLE_AUDIENCE


def _from_ayrshare_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Best-effort map of Ayrshare /history records to our post shape."""
    out = []
    for h in history:
        analytics = h.get("analytics", {}) or {}
        out.append(
            {
                "posted": h.get("created") or h.get("scheduleDate") or "",
                "caption": h.get("post", "")[:120],
                "views": int(analytics.get("videoViews", analytics.get("views", 0)) or 0),
                "likes": int(analytics.get("likeCount", analytics.get("likes", 0)) or 0),
                "comments": int(analytics.get("commentCount", analytics.get("comments", 0)) or 0),
                "shares": int(analytics.get("shareCount", analytics.get("shares", 0)) or 0),
            }
        )
    return out


def _from_ayrshare_analytics(data: dict[str, Any]) -> dict[str, Any]:
    tt = (data or {}).get("tiktok", {})
    analytics = tt.get("analytics", tt) if isinstance(tt, dict) else {}
    if not analytics:
        return {}
    return {
        "followers": analytics.get("followerCount", analytics.get("followers", 0)),
        "growth_30d": analytics.get("followerCountChange", "n/a"),
        "top_locations": analytics.get("topLocations", []),
        "age_skew": analytics.get("ageRange", "n/a"),
        "gender_skew": analytics.get("gender", "n/a"),
        "active_hours": analytics.get("activeHours", "n/a"),
        "top_themes": [],
    }


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
