"""Every morning: scan Gmail for new leads, log them in a Sheet, and draft
intro replies."""

from __future__ import annotations

from datetime import date

from ..core import Agent, AgentResult, Context, register

_SCHEMA = {
    "type": "object",
    "properties": {
        "leads": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "intent": {"type": "string"},
                    "hotness": {"type": "string", "enum": ["hot", "warm", "cold"]},
                    "draft_reply": {"type": "string"},
                },
                "required": ["id", "name", "email", "intent", "hotness", "draft_reply"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["leads"],
    "additionalProperties": False,
}


@register
class CaptureLeads(Agent):
    name = "capture_leads"
    description = "Capture leads automatically"

    def run(self, ctx: Context) -> AgentResult:
        unread = ctx.gmail.unread(max_results=30)
        already = set(ctx.state.get("logged", []))

        system = (
            "You identify sales leads in an inbox for a "
            f"{ctx.business.niche} studio.\n{ctx.business.as_prompt()}\n"
            "A lead is anyone expressing interest in services, rates, availability, "
            "or a project. Ignore newsletters, receipts, and automated mail. "
            "Draft a warm, specific intro reply for each lead."
        )
        prompt = (
            "Find the genuine leads in these emails. For non-leads, omit them.\n\n"
            + "\n".join(
                f"[{m['id']}] from {m['from']} — {m['subject']}: {m['snippet']}"
                for m in unread
            )
        )
        result = ctx.llm.complete_json(prompt, _SCHEMA, system=system, max_tokens=4000)
        leads = [l for l in result.get("leads", []) if l["id"] not in already]

        if not leads:
            return AgentResult(title="🧲 Lead capture", body="No new leads today.")

        rows = [
            [str(date.today()), l["name"], l["email"], l["intent"], l["hotness"]]
            for l in leads
        ]
        drafts = [
            {"to": l["email"], "subject": "Re: your enquiry", "body": l["draft_reply"]}
            for l in leads
        ]
        for l in leads:
            ctx.state.append("logged", l["id"], cap=1000)

        body = f"Logged {len(leads)} new lead(s) to your sheet and drafted replies:\n\n" + "\n".join(
            f"• {l['name']} ({l['hotness'].upper()}) — {l['intent']}" for l in leads
        )
        return AgentResult(
            title=f"🧲 {len(leads)} new lead(s) captured",
            body=body,
            data={
                "rows": rows,
                "sheet_id": ctx.integrations.sheets.env("LEADS_SHEET_ID", "") or "",
                "tab": "Leads",
                "drafts": drafts,
            },
        )
