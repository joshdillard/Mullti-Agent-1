"""Every night: hunt for companies that fit my client profile, find the right
contact, and draft an email I can send in the morning."""

from __future__ import annotations

from ..core import Agent, AgentResult, Context, register


@register
class FindNewClients(Agent):
    name = "find_new_clients"
    description = "Find new clients while I sleep"

    def run(self, ctx: Context) -> AgentResult:
        n = int(ctx.config.get("targets_per_run", 10))
        profile = ctx.config.get(
            "client_profile",
            f"Growing brands that need ongoing short-form video and {ctx.business.niche}",
        )
        companies = ctx.linkedin.search_companies(profile, limit=n)
        contacted = set(ctx.state.get("contacted", []))
        fresh = [c for c in companies if c["name"] not in contacted]
        if not fresh:
            return AgentResult(
                title="🌙 New clients", body="No new-fit companies tonight."
            )

        system = (
            "You are a B2B outbound specialist for a "
            f"{ctx.business.niche} studio.\n{ctx.business.as_prompt()}\n"
            "Emails are short (under 120 words), specific to the company's signal, "
            "lead with value, and end with a soft ask. No fluff, no 'I hope this finds you well'."
        )
        drafts = []
        lines = []
        for c in fresh:
            prompt = (
                f"Write a cold email to {c['contact']} ({c['title']}) at "
                f"{c['name']} — a {c['size']} {c['industry']} company. "
                f"Signal worth referencing: {c['signal']}. "
                "Goal: book a 15-min discovery call. Return just subject + body."
            )
            email = ctx.llm.complete(prompt, system=system, max_tokens=600)
            subject, draft_body = _split_subject(email)
            drafts.append(
                {
                    "to": f"{c['contact']} <unknown@{_domain(c['name'])}>",
                    "subject": subject,
                    "body": draft_body,
                }
            )
            lines.append(f"• {c['name']} — {c['contact']} ({c['title']}) — {c['signal']}")
            ctx.state.append("contacted", c["name"], cap=500)

        body = (
            f"Found {len(fresh)} new-fit companies and drafted emails (in your "
            "Gmail drafts, ready to review & send):\n\n" + "\n".join(lines)
        )
        return AgentResult(
            title=f"🌙 {len(fresh)} new client prospects",
            body=body,
            data={"drafts": drafts},
        )


def _split_subject(email: str) -> tuple[str, str]:
    lines = [l for l in email.splitlines() if l.strip()]
    if lines and lines[0].lower().startswith("subject"):
        subject = lines[0].split(":", 1)[-1].strip()
        return subject, "\n".join(lines[1:]).strip()
    return "Quick idea for your team", email.strip()


def _domain(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum()) + ".com"
