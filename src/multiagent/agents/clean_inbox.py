"""Every morning: sort unread emails into reply-today / FYI / archive, and
draft the urgent replies."""

from __future__ import annotations

from ..core import Agent, AgentResult, Context, register

_SCHEMA = {
    "type": "object",
    "properties": {
        "reply_today": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "from": {"type": "string"},
                    "subject": {"type": "string"},
                    "why": {"type": "string"},
                    "draft_reply": {"type": "string"},
                },
                "required": ["id", "from", "subject", "why", "draft_reply"],
                "additionalProperties": False,
            },
        },
        "fyi": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "subject": {"type": "string"},
                },
                "required": ["id", "subject"],
                "additionalProperties": False,
            },
        },
        "archive": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "subject": {"type": "string"},
                },
                "required": ["id", "subject"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["reply_today", "fyi", "archive"],
    "additionalProperties": False,
}


@register
class CleanInbox(Agent):
    name = "clean_inbox"
    description = "Clean my inbox daily"

    def run(self, ctx: Context) -> AgentResult:
        unread = ctx.gmail.unread(max_results=30)
        if not unread:
            return AgentResult(title="📥 Inbox", body="Inbox zero — nothing unread.")

        system = (
            "You are an executive assistant for the owner of a "
            f"{ctx.business.niche} business.\n{ctx.business.as_prompt()}\n"
            "Triage ruthlessly. 'reply_today' is for client/revenue/time-sensitive "
            "mail only. Draft replies in the owner's voice: friendly, brief, concrete."
        )
        prompt = "Triage these unread emails:\n" + "\n".join(
            f"[{m['id']}] from {m['from']} — {m['subject']}: {m['snippet']}"
            for m in unread
        )
        triage = ctx.llm.complete_json(prompt, _SCHEMA, system=system, max_tokens=4000)

        # Build Gmail drafts for the urgent ones.
        by_id = {m["id"]: m for m in unread}
        drafts = []
        for item in triage.get("reply_today", []):
            sender = by_id.get(item["id"], {}).get("from", item.get("from", ""))
            drafts.append(
                {
                    "to": sender,
                    "subject": "Re: " + item["subject"],
                    "body": item["draft_reply"],
                }
            )

        body = _render(triage)
        return AgentResult(
            title="📥 Inbox triaged",
            body=body,
            data={"drafts": drafts},
        )


def _render(t: dict) -> str:
    out = []
    rt = t.get("reply_today", [])
    out.append(f"🔴 Reply today ({len(rt)}):")
    for i in rt:
        out.append(f"  • {i['from']} — {i['subject']}  ({i['why']})")
    fyi = t.get("fyi", [])
    out.append(f"\n🟡 FYI ({len(fyi)}):")
    for i in fyi:
        out.append(f"  • {i['subject']}")
    arch = t.get("archive", [])
    out.append(f"\n⚪ Archive ({len(arch)}):")
    for i in arch:
        out.append(f"  • {i['subject']}")
    out.append("\nDrafts for the urgent replies are in your Gmail drafts folder.")
    return "\n".join(out)
