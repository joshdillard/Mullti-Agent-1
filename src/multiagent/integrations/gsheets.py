"""Google Sheets adapter — append rows (leads, metrics, expenses)."""

from __future__ import annotations

from typing import Any

from .base import Integration
from ._google import google_service


class Sheets(Integration):
    name = "sheets"
    env_vars = ("GOOGLE_CREDENTIALS_FILE",)

    def append_rows(self, spreadsheet_id: str, rows: list[list[Any]], tab: str = "Sheet1") -> dict[str, Any]:
        if not self.configured or not spreadsheet_id:
            self.demo("append_rows")
            self.log.info("would append %d row(s) to sheet %s", len(rows), spreadsheet_id or "<none>")
            return {"status": "demo", "rows": len(rows)}
        svc = google_service("sheets", "v4")
        if svc is None:
            self.demo("append_rows")
            return {"status": "demo", "rows": len(rows)}
        result = (
            svc.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=f"{tab}!A1",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": rows},
            )
            .execute()
        )
        return {"status": "ok", "updates": result.get("updates", {})}

    def read(self, spreadsheet_id: str, rng: str) -> list[list[Any]]:
        if not self.configured or not spreadsheet_id:
            self.demo("read")
            return []
        svc = google_service("sheets", "v4")
        if svc is None:
            return []
        result = (
            svc.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=rng).execute()
        )
        return result.get("values", [])
