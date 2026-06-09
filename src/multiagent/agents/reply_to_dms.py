"""Read my unread DMs across platforms, draft a reply to each, and (optionally)
send them. Powered by Zernio's inbox API.

Safety: replies are DRAFTED by default and shown to you. They only auto-send
if you set ZERNIO_AUTO_SEND=true in .env.
"""

from __future__ import annotations

from ..core import Agent, AgentResult, Context, register

_SCHEMA = {
    "type": "object",
    "properties": {
        "replies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "participant": {"type": "string"},
                    "platform": {"type": "string"},
                    "intent": {"type": "string"},
                    "hotness": {"type": "string", "enum": ["lead", "fan", "spam", "other"]},
                    "draft": {"type": "string"},
                },
                "required": ["id", "participant", "platform", "intent", "hotness", "draft"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["replies"],
    "additionalProperties": False,
}


@register
class ReplyToDMs(Agent):
    name = "reply_to_dms"
    description = "Reply to my DMs"

    def run(self, ctx: Context) -> AgentResult:
        convos = ctx.zernio.unread_conversations(limit=25)
        if not convos:
            return AgentResult(title="💬 DMs", body="No unread DMs right now.")

        system = (
            "You manage DMs for the owner of a "
            f"{ctx.business.niche} business.\n{ctx.business.as_prompt()}\n"
            "Draft a reply for each message in the owner's voice: friendly, brief, "
            "and helpful. If it's a potential client, move toward a call or rates. "
            "If it's spam, draft nothing useful and mark it 'spam'."
        )
        prompt = "Draft a reply to each of these DMs:\n" + "\n".join(
            f"[{c['id']}] {c['participant']} on {c['platform']}: {c['last_message']}"
            for c in convos
        )
        result = ctx.llm.complete_json(prompt, _SCHEMA, system=system, max_tokens=4000)
        replies = [r for r in result.get("replies", []) if r["hotness"] != "spam"]

        sent = 0
        for r in replies:
            out = ctx.zernio.send_message(r["id"], r["draft"])
            if out.get("status") == "ok":
                sent += 1

        auto = ctx.zernio.auto_send
        verb = f"Sent {sent}" if auto else f"Drafted {len(replies)}"
        lines = [
            f"• {r['participant']} ({r['platform']}, {r['hotness']}): {r['intent']}\n"
            f"   ↳ \"{r['draft']}\""
            for r in replies
        ]
        note = (
            "" if auto
            else "\n\n(These are drafts. Set ZERNIO_AUTO_SEND=true in .env to auto-send.)"
        )
        return AgentResult(
            title=f"💬 {verb} DM repl{'y' if len(replies)==1 else 'ies'}",
            body="\n\n".join(lines) + note,
        )
