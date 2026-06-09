"""Every Monday: pull last week's Stripe numbers vs the prior week and surface
what changed."""

from __future__ import annotations

from ..core import Agent, AgentResult, Context, register


@register
class WeeklyRevenueSummary(Agent):
    name = "weekly_revenue_summary"
    description = "Send me a weekly revenue summary"

    def run(self, ctx: Context) -> AgentResult:
        rev = ctx.stripe.weekly_revenue()
        last_snapshot = ctx.state.get("last_week_value")

        arrow = "▲" if rev["delta"] >= 0 else "▼"
        headline = (
            f"{arrow} ${rev['this_week']:,.0f} this week "
            f"(vs ${rev['prior_week']:,.0f} — {rev['pct_change']:+.1f}%)"
        )

        system = (
            "You are a fractional CFO for a "
            f"{ctx.business.niche} business.\n{ctx.business.as_prompt()}\n"
            "Be brief and decision-oriented."
        )
        prompt = (
            f"This week: ${rev['this_week']:,.2f}. Prior week: ${rev['prior_week']:,.2f}. "
            f"Change: ${rev['delta']:,.2f} ({rev['pct_change']:+.1f}%).\n"
            + (
                f"Two weeks ago the running snapshot was ${last_snapshot:,.2f}.\n"
                if isinstance(last_snapshot, (int, float))
                else ""
            )
            + "In 4-6 sentences: what changed, the most likely driver, and the one "
            "thing to focus on this week to keep/accelerate the trend."
        )
        body = ctx.llm.complete(prompt, system=system, max_tokens=1000)
        ctx.state.set("last_week_value", rev["this_week"])

        return AgentResult(
            title=f"💰 Weekly revenue — {headline}",
            body=body,
        )
