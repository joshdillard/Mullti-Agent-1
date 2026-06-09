"""LinkedIn adapter — draft posts, search roles/companies, competitor pages.

Live mode uses LINKEDIN_ACCESS_TOKEN against the LinkedIn Marketing / Posts
APIs. We deliberately *draft* rather than auto-post outward content.
"""

from __future__ import annotations

from typing import Any

from .base import Integration


class LinkedIn(Integration):
    name = "linkedin"
    env_vars = ("LINKEDIN_ACCESS_TOKEN",)

    def draft_post(self, text: str) -> dict[str, Any]:
        """Stage a post as a draft (never auto-published)."""
        if not self.configured:
            self.demo("draft_post")
            return {"status": "demo", "text": text}
        # Live: POST /rest/posts with lifecycleState=DRAFT.
        raise NotImplementedError("Wire LinkedIn Posts API (draft) here.")

    def search_companies(self, profile: str, limit: int = 10) -> list[dict[str, Any]]:
        """Find companies matching an ideal-client profile."""
        if not self.configured:
            self.demo("search_companies")
            return _SAMPLE_COMPANIES[:limit]
        raise NotImplementedError("Wire LinkedIn company search here.")

    def search_roles(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if not self.configured:
            self.demo("search_roles")
            return _SAMPLE_ROLES[:limit]
        raise NotImplementedError("Wire LinkedIn jobs search here.")

    def competitor_activity(self, handle: str) -> dict[str, Any]:
        if not self.configured:
            self.demo("competitor_activity")
            return {
                "handle": handle,
                "recent_posts": [
                    {"text": "Launched a new short-form retainer package", "likes": 320},
                    {"text": "Case study: 4M views for a SaaS client", "likes": 540},
                ],
                "headcount_change": "+2 editors",
                "cadence": "4 posts/week",
            }
        raise NotImplementedError("Wire LinkedIn organization activity here.")


_SAMPLE_COMPANIES = [
    {"name": "BrightPath SaaS", "industry": "B2B software", "size": "50-200",
     "contact": "Dana Liu", "title": "Head of Marketing", "signal": "hiring a content lead"},
    {"name": "Northwind DTC", "industry": "E-commerce", "size": "11-50",
     "contact": "Marcus Reed", "title": "Founder", "signal": "ramping paid social"},
    {"name": "Cedar Health", "industry": "Healthtech", "size": "200-500",
     "contact": "Priya Nair", "title": "Brand Director", "signal": "rebrand in progress"},
]

_SAMPLE_ROLES = [
    {"title": "Head of Content", "company": "Vector Labs", "posted": "2 days ago",
     "location": "Remote (US)"},
    {"title": "Senior Video Producer", "company": "Lumen Media", "posted": "4 days ago",
     "location": "New York, NY"},
]
