"""Gmail adapter — read unread mail, draft replies, scan for leads.

Live mode uses the Gmail API via google-api-python-client with OAuth
credentials at GOOGLE_CREDENTIALS_FILE. Drafts are created, never sent
automatically.
"""

from __future__ import annotations

from typing import Any

from .base import Integration
from ._google import google_service


class Gmail(Integration):
    name = "gmail"
    env_vars = ("GOOGLE_CREDENTIALS_FILE",)

    def unread(self, max_results: int = 25) -> list[dict[str, Any]]:
        if not self.configured:
            self.demo("unread")
            return _SAMPLE_UNREAD[:max_results]
        svc = google_service("gmail", "v1")
        if svc is None:
            self.demo("unread")
            return _SAMPLE_UNREAD[:max_results]
        # Live: users().messages().list(q="is:unread") then .get() per id.
        raise NotImplementedError("Wire Gmail messages.list(is:unread) here.")

    def create_draft(self, to: str, subject: str, body: str) -> dict[str, Any]:
        if not self.configured:
            self.demo("create_draft")
            return {"status": "demo", "to": to, "subject": subject}
        # Live: users().drafts().create(...)
        raise NotImplementedError("Wire Gmail drafts.create here.")


_SAMPLE_UNREAD = [
    {"id": "1", "from": "dana@brightpath.io", "subject": "Interested in a retainer",
     "snippet": "Saw your reel — we need ongoing short-form for Q3. Can you send rates?"},
    {"id": "2", "from": "newsletter@tooly.com", "subject": "Weekly product digest",
     "snippet": "This week in product..."},
    {"id": "3", "from": "marcus@northwind.co", "subject": "Quick question on turnaround",
     "snippet": "If we book 8 videos, what's your typical delivery time?"},
    {"id": "4", "from": "billing@adobe.com", "subject": "Your receipt",
     "snippet": "Thanks for your payment of $59.99"},
    {"id": "5", "from": "noreply@calendly.com", "subject": "New event booked",
     "snippet": "Discovery call confirmed for Thursday 2pm"},
]
