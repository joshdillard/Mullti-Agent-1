"""Every quarter: pull income and expenses into a Sheet organized for my
accountant."""

from __future__ import annotations

from datetime import date

from ..core import Agent, AgentResult, Context, register


@register
class TaxSeasonPrep(Agent):
    name = "tax_season_prep"
    description = "Prepare me for tax season"

    def run(self, ctx: Context) -> AgentResult:
        q = ctx.stripe.quarterly_breakdown()

        system = (
            "You are a bookkeeper preparing a quarterly summary for an accountant, "
            f"for a {ctx.business.niche} business.\n{ctx.business.as_prompt()}\n"
            "Be precise and accountant-friendly. Flag anything that needs a receipt "
            "or a categorization decision."
        )
        prompt = (
            f"Quarterly Stripe data:\n"
            f"- Gross income: ${q['income']:,.2f}\n"
            f"- Stripe fees: ${q['stripe_fees']:,.2f}\n"
            f"- Refunds: ${q['refunds']:,.2f}\n"
            f"- Net: ${q['net']:,.2f}\n"
            f"- Top clients: {q['top_clients']}\n\n"
            "Write a short note for my accountant: summary of the quarter, what's "
            "included, what's NOT included (e.g. non-Stripe income, software/gear "
            "expenses to add), and a checklist of what I should hand over."
        )
        note = ctx.llm.complete(prompt, system=system, max_tokens=1800)

        rows = [
            [str(date.today()), "Gross income", q["income"]],
            [str(date.today()), "Stripe fees", -q["stripe_fees"]],
            [str(date.today()), "Refunds", -q["refunds"]],
            [str(date.today()), "Net (Stripe)", q["net"]],
        ]
        return AgentResult(
            title="🧾 Quarterly tax prep",
            body=note,
            data={
                "rows": rows,
                "sheet_id": ctx.integrations.sheets.env("TAX_SHEET_ID", "") or "",
                "tab": "Quarterly",
            },
        )
