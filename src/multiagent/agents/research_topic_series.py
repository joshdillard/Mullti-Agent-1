"""Research a topic deeply and turn it into a 5-part series with scripts,
hooks, and posting order — delivered to a Google Doc."""

from __future__ import annotations

from ..core import Agent, AgentResult, Context, register


@register
class ResearchTopicSeries(Agent):
    name = "research_topic_series"
    description = "Research a topic and plan content"

    def run(self, ctx: Context) -> AgentResult:
        topic = ctx.params.get("topic") or _default_topic(ctx)
        parts = int(ctx.config.get("parts", 5))

        system = (
            "You are a senior content researcher and short-form scriptwriter for a "
            f"{ctx.business.niche} brand.\n{ctx.business.as_prompt()}\n"
            "Research is grounded and current; scripts are tight and hook-first."
        )
        prompt = (
            f"Research the topic: \"{topic}\".\n"
            "Use web search to ground it in current facts, examples, and what's "
            "already saturated vs underexplored.\n\n"
            f"Then design a {parts}-part short-form video series. Produce a "
            "Google-Doc-ready document with:\n"
            "1. A short research brief (key facts, angles, what competitors miss)\n"
            f"2. The {parts} episodes, each with:\n"
            "   - Working title\n"
            "   - Hook (first 2 seconds, verbatim)\n"
            "   - Full script (spoken lines + on-screen text + b-roll notes)\n"
            "   - Caption + 3-5 hashtags\n"
            "3. Recommended posting order and cadence, and why.\n"
            "Format with clear headings."
        )
        body = ctx.llm.complete(
            prompt, system=system, max_tokens=14000, web_search=True
        )

        return AgentResult(
            title=f"{ctx.business.name} — Series: {topic}",
            body=body,
            data={"topic": topic},
        )


def _default_topic(ctx: Context) -> str:
    aud = ctx.tiktok.audience()
    themes = aud.get("top_themes", [])
    if themes:
        return themes[0]["theme"]
    return f"getting started in {ctx.business.niche}"
