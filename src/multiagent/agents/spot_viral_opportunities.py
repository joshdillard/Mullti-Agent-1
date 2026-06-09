"""Monitor TikTok trends and ping me when something in my niche starts
blowing up."""

from __future__ import annotations

from ..core import Agent, AgentResult, Context, register


@register
class SpotViralOpportunities(Agent):
    name = "spot_viral_opportunities"
    description = "Spot viral opportunities"

    def run(self, ctx: Context) -> AgentResult:
        keywords = ctx.config.get("niche_keywords", [])
        trends = ctx.tiktok.trending(keywords=keywords, limit=12)
        seen = set(ctx.state.get("pinged", []))

        # Only surface fast-rising trends we haven't already flagged.
        rising = [
            t for t in trends
            if _is_rising(t) and t.get("name") not in seen
        ]
        if not rising:
            return AgentResult(
                title="📈 Trend sweep",
                body="No new fast-rising trends in your niche right now. Holding.",
            )

        system = (
            "You are a trend scout for a "
            f"{ctx.business.niche} creator.\n{ctx.business.as_prompt()}\n"
            "For each opportunity, say in one line how to jump on it TODAY."
        )
        prompt = (
            "These niche trends are accelerating right now:\n"
            + "\n".join(f"- {t['name']} (growth {t.get('growth','?')})" for t in rising)
            + "\n\nFor each, give: the trend, why it fits this creator, and a "
            "ready-to-shoot angle. Keep it punchy — this is a phone alert."
        )
        body = ctx.llm.complete(prompt, system=system, max_tokens=1200)

        for t in rising:
            if t.get("name"):
                ctx.state.append("pinged", t["name"], cap=100)

        return AgentResult(title="🚨 Viral opportunity spotted", body=body)


def _is_rising(trend: dict) -> bool:
    growth = str(trend.get("growth", "")).strip("+%")
    try:
        return float(growth) >= 100
    except ValueError:
        return False
