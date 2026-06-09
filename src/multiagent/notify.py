"""Delivery layer.

An agent populates an AgentResult (title, body, and optional structured
payloads in `data`) and declares its destinations in config via `deliver_to`.
The Notifier routes the result to each channel. This keeps agent bodies free
of plumbing — they describe *what* to produce, not *where* it goes.

Supported channels (match the dashboard card icons):
  telegram        -> push title + body to Telegram
  console         -> always-on local print (default)
  gdoc            -> create a Google Doc from title + body
  sheet           -> append data["rows"] to data["sheet_id"]
  gmail_draft     -> create drafts from data["drafts"] = [{to,subject,body}]
  linkedin_draft  -> stage data["linkedin_post"] as a LinkedIn draft
"""

from __future__ import annotations

import logging

log = logging.getLogger("multiagent.notify")


class Notifier:
    def __init__(self, integrations, deliver_to: list[str]) -> None:
        self.ix = integrations
        self.channels = list(deliver_to or [])

    def send(self, result) -> None:
        """Route a finished AgentResult to its configured channels."""
        # Console is always on so a local/cron run shows something.
        self._console(result)

        if not result.ok:
            # On failure still ping Telegram if configured, then stop.
            if "telegram" in self.channels:
                if self.ix.telegram.send(f"⚠️ {result.title}\n{result.error}"):
                    result.delivered_to.append("telegram")
            return

        for ch in self.channels:
            try:
                handler = getattr(self, f"_{ch}", None)
                if handler is None:
                    log.warning("unknown channel '%s' — skipping", ch)
                    continue
                if handler(result):
                    result.delivered_to.append(ch)
            except Exception:  # noqa: BLE001
                log.exception("delivery to %s failed", ch)

    # --- channels -----------------------------------------------------------
    def _console(self, result) -> bool:
        print("\n" + "=" * 70)
        print(result.title)
        print("=" * 70)
        if result.body:
            print(result.body)
        print()
        return True

    def _telegram(self, result) -> bool:
        text = result.title
        if result.body:
            text += "\n\n" + result.body
        return self.ix.telegram.send(text)

    def _gdoc(self, result) -> bool:
        out = self.ix.docs.create(result.title, result.body)
        ref = out.get("url") or out.get("path")
        if ref:
            result.data.setdefault("doc_ref", ref)
        return True

    def _sheet(self, result) -> bool:
        rows = result.data.get("rows")
        sheet_id = result.data.get("sheet_id", "")
        if not rows:
            return False
        self.ix.sheets.append_rows(sheet_id, rows, result.data.get("tab", "Sheet1"))
        return True

    def _gmail_draft(self, result) -> bool:
        drafts = result.data.get("drafts", [])
        if not drafts:
            return False
        for d in drafts:
            self.ix.gmail.create_draft(d["to"], d["subject"], d["body"])
        return True

    def _linkedin_draft(self, result) -> bool:
        text = result.data.get("linkedin_post")
        if not text:
            return False
        self.ix.linkedin.draft_post(text)
        return True
