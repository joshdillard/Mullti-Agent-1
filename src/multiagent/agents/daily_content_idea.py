"""Every morning at 8am: one fresh content idea based on what's trending and
what I've already made."""

from __future__ import annotations

from ..core import Agent, AgentResult, Context, register


@register
class DailyContentIdea(Agent):
    name = "daily_content_idea"
    description = "Daily content idea"

    def run(self, ctx: Context) -> AgentResult:
        trends = ctx.tiktok.trending(limit=8)
        recent = ctx.tiktok.my_recent_posts(days=14)
        already_suggested = ctx.state.get("past_ideas", [])

        system = (
            "You are a sharp short-form content strategist for a "
            f"{ctx.business.niche} business.\n{ctx.business.as_prompt()}\n"
            "Give ONE idea the creator can shoot today. Be specific and original; "
            "do not repeat past ideas."
        )
        prompt = (
            "Today's trending formats/sounds/hashtags:\n"
            + "\n".join(f"- {t}" for t in trends)
            + "\n\nWhat I've recently posted (don't repeat these angles):\n"
            + "\n".join(f"- {p['caption']} ({p['views']:,} views)" for p in recent)
            + "\n\nIdeas already suggested this month (avoid):\n"
            + ("\n".join(f"- {i}" for i in already_suggested[-20:]) or "- (none yet)")
            + "\n\nReturn:\n"
            "1. HOOK (the first 2 seconds, said out loud)\n"
            "2. CONCEPT (1-2 sentences)\n"
            "3. WHY NOW (which trend it rides)\n"
            "4. A LinkedIn text-post version of the same idea (3-5 lines, no hashtags)."
        )
        body = ctx.llm.complete(prompt, system=system, max_tokens=1500)

        # Remember a one-line label so we don't repeat it tomorrow.
        label = body.splitlines()[0][:120] if body else ""
        ctx.state.append("past_ideas", label, cap=60)

        # Split the LinkedIn variant out for the linkedin_draft channel.
        linkedin_post = _extract_linkedin(body)

        return AgentResult(
            title="🎬 Today's content idea",
            body=body,
            data={"linkedin_post": linkedin_post},
        )


def _extract_linkedin(text: str) -> str:
    low = text.lower()
    idx = low.find("linkedin")
    if idx == -1:
        return ""
    after = text[idx:]
    nl = after.find("\n")
    return after[nl + 1 :].strip() if nl != -1 else ""
