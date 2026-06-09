"""Every day: scan TikTok and the web for mentions of my company and summarize
the sentiment."""

from __future__ import annotations

from ..core import Agent, AgentResult, Context, register


@register
class TrackBrandMentions(Agent):
    name = "track_brand_mentions"
    description = "Track brand mentions daily"

    def run(self, ctx: Context) -> AgentResult:
        name = ctx.business.name
        handle = ctx.business.handle

        system = (
            "You are a brand-monitoring analyst.\n"
            f"{ctx.business.as_prompt()}\n"
            "Search the web (and reason about social) for recent mentions of this "
            "brand. Summarize what people are saying and the overall sentiment. "
            "If you find nothing credible, say so plainly rather than inventing mentions."
        )
        prompt = (
            f"Find mentions from the last 24-48 hours of the brand \"{name}\" "
            f"(handle {handle}). Cover the web and any discoverable social chatter.\n\n"
            "Return:\n"
            "1. Sentiment overall (positive / neutral / negative + a 1-line read)\n"
            "2. Notable mentions (who, where, what they said)\n"
            "3. Anything needing a response today\n"
            "4. One opportunity (a fan to engage, a thread to join)."
        )
        body = ctx.llm.complete(prompt, system=system, max_tokens=2000, web_search=True)
        return AgentResult(title=f"🗣️ Brand mentions — {name}", body=body)
