"""Analyze my followers and top-performing posts and tell me who my actual
audience is and what they want."""

from __future__ import annotations

from ..core import Agent, AgentResult, Context, register


@register
class ResearchAudience(Agent):
    name = "research_audience"
    description = "Research my audience"

    def run(self, ctx: Context) -> AgentResult:
        aud = ctx.tiktok.audience()
        posts = ctx.tiktok.my_recent_posts(days=30)
        top = sorted(posts, key=lambda p: p["views"], reverse=True)[:5]

        system = (
            "You are an audience researcher for a "
            f"{ctx.business.niche} creator.\n{ctx.business.as_prompt()}\n"
            "Translate raw numbers into a clear picture of WHO follows and WHAT they want."
        )
        prompt = (
            f"Audience data:\n{_fmt(aud)}\n\n"
            "Top posts (last 30 days):\n"
            + "\n".join(f"- {p['caption']} ({p['views']:,} views)" for p in top)
            + "\n\nTell me:\n"
            "1. Who my actual audience is (a 2-3 sentence persona)\n"
            "2. What they clearly want more of (evidence from top posts)\n"
            "3. What they're NOT responding to\n"
            "4. 3 content bets tailored to them\n"
            "5. One way to convert this audience into paying clients."
        )
        body = ctx.llm.complete(prompt, system=system, max_tokens=2200)
        return AgentResult(title="👥 Who your audience actually is", body=body)


def _fmt(d: dict) -> str:
    lines = []
    for k, v in d.items():
        if isinstance(v, list):
            v = "; ".join(
                x.get("theme", str(x)) if isinstance(x, dict) else str(x) for x in v
            )
        lines.append(f"- {k}: {v}")
    return "\n".join(lines)
