"""Google Docs adapter — create a doc from markdown-ish text.

Live mode creates a Doc in Drive and returns its URL. Demo mode writes the
content to a local file under state/docs/ so you still get the deliverable.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .base import Integration
from ._google import google_service
from ..settings import ROOT


class Docs(Integration):
    name = "docs"
    env_vars = ("GOOGLE_CREDENTIALS_FILE",)

    def create(self, title: str, body: str) -> dict[str, Any]:
        if not self.configured:
            return self._local(title, body)
        svc = google_service("docs", "v1")
        if svc is None:
            return self._local(title, body)
        doc = svc.documents().create(body={"title": title}).execute()
        doc_id = doc["documentId"]
        svc.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [{"insertText": {"location": {"index": 1}, "text": body}}]},
        ).execute()
        url = f"https://docs.google.com/document/d/{doc_id}/edit"
        self.log.info("created Google Doc: %s", url)
        return {"status": "ok", "url": url, "id": doc_id}

    def _local(self, title: str, body: str) -> dict[str, Any]:
        self.demo("create")
        out_dir = ROOT / "state" / "docs"
        out_dir.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60] or "doc"
        path = Path(out_dir / f"{slug}.md")
        path.write_text(f"# {title}\n\n{body}\n")
        self.log.info("wrote doc locally: %s", path)
        return {"status": "demo", "path": str(path)}
