"""Search senior roles posted this week, tailor my CV for each, and draft
intro messages to hiring managers. (Off by default — enable in config.)"""

from __future__ import annotations

from ..core import Agent, AgentResult, Context, register


@register
class FindNextRole(Agent):
    name = "find_next_role"
    description = "Find my next role"

    def run(self, ctx: Context) -> AgentResult:
        query = ctx.params.get("query") or ctx.config.get(
            "role_query", "Head of Content OR Senior Video Producer"
        )
        roles = ctx.linkedin.search_roles(query, limit=5)
        if not roles:
            return AgentResult(title="💼 Roles", body="No new senior roles this week.")

        system = (
            "You are a career coach and copywriter.\n"
            "Tailor positioning crisply; intro messages are short, specific, and "
            "reference the role. Never fabricate experience."
        )
        prompt = (
            "For each role below, give: (a) the 2-3 CV bullet points to emphasize, "
            "(b) a 4-sentence intro DM to the hiring manager.\n\nRoles:\n"
            + "\n".join(
                f"- {r['title']} @ {r['company']} ({r['location']}, {r['posted']})"
                for r in roles
            )
        )
        body = ctx.llm.complete(prompt, system=system, max_tokens=3000)
        return AgentResult(title="💼 5 roles + tailored intros", body=body)
