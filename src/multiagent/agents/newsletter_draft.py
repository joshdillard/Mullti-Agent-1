"""Every Friday: pull the week's posts and draft a newsletter I can send to
my list — delivered to a Google Doc."""

from __future__ import annotations

from ..core import Agent, AgentResult, Context, register


@register
class NewsletterDraft(Agent):
    name = "newsletter_draft"
    description = "Newsletter draft from my content"

    def run(self, ctx: Context) -> AgentResult:
        posts = ctx.tiktok.my_recent_posts(days=7)

        system = (
            "You are a newsletter writer for a "
            f"{ctx.business.niche} creator.\n{ctx.business.as_prompt()}\n"
            "Voice: warm, useful, no fluff. The reader is a fan and potential client."
        )
        prompt = (
            "Turn this week's posts into a newsletter the creator can send today:\n"
            + "\n".join(
                f"- {p['caption']} ({p['views']:,} views)" for p in posts
            )
            + "\n\nStructure:\n"
            "- Subject line (and 1 alternate)\n"
            "- A short personal intro (2-3 sentences)\n"
            "- 'This week's drops' — recap each post with the lesson/takeaway and a CTA to watch\n"
            "- One practical tip readers can use even if they didn't watch\n"
            "- A soft CTA (reply, book a call, or share)\n"
            "Keep it scannable."
        )
        body = ctx.llm.complete(prompt, system=system, max_tokens=4000)

        return AgentResult(
            title=f"{ctx.business.name} — Newsletter draft",
            body=body,
        )
