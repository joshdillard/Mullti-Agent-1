"""Every Monday: check competitors' websites, pricing, TikTok and LinkedIn for
changes, and send me a brief."""

from __future__ import annotations

from ..core import Agent, AgentResult, Context, register


@register
class TrackCompetitors(Agent):
    name = "track_competitors"
    description = "Track my competitors"

    def run(self, ctx: Context) -> AgentResult:
        competitors = ctx.config.get("competitors", [])
        if not competitors:
            return AgentResult(
                title="🔍 Competitor watch",
                body="No competitors configured. Add handles/domains under "
                "track_competitors.competitors in config/agents.yaml.",
            )

        # Gather LinkedIn signals per competitor (live or sampled).
        signals = []
        for c in competitors:
            act = ctx.linkedin.competitor_activity(c)
            signals.append(f"{c}: {act}")

        system = (
            "You are a competitive-intelligence analyst for a "
            f"{ctx.business.niche} business.\n{ctx.business.as_prompt()}\n"
            "Use web search to check each competitor's current site, pricing, and "
            "recent social activity. Flag only what CHANGED or matters."
        )
        prompt = (
            "Competitors to brief on: "
            + ", ".join(competitors)
            + "\n\nKnown social signals:\n"
            + "\n".join(f"- {s}" for s in signals)
            + "\n\nSearch each competitor's website + pricing + recent posts. "
            "Give a tight Monday brief: what changed, pricing moves, content "
            "themes they're winning with, and 2 openings for us to exploit."
        )
        body = ctx.llm.complete(prompt, system=system, max_tokens=2500, web_search=True)
        return AgentResult(title="🔍 Competitor brief", body=body)
