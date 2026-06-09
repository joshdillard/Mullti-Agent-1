"""Shared Google API client builder.

Returns an authorized service for Gmail/Sheets/Docs, or None when the
google client libraries or credentials aren't available (so callers fall
back to demo mode cleanly).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

log = logging.getLogger("multiagent.integration.google")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]


def google_service(api: str, version: str):
    """Build an authorized Google API service, or None if unavailable."""
    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "")
    if not creds_file or not Path(creds_file).exists():
        return None
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        log.info(
            "google client libraries not installed — "
            "`pip install google-api-python-client google-auth-oauthlib`"
        )
        return None

    token_file = os.getenv("GOOGLE_TOKEN_FILE", "credentials/google_token.json")
    creds = None
    if Path(token_file).exists():
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        try:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
            Path(token_file).parent.mkdir(parents=True, exist_ok=True)
            Path(token_file).write_text(creds.to_json())
        except Exception as exc:  # noqa: BLE001
            log.warning("google auth failed: %s", exc)
            return None
    return build(api, version, credentials=creds, cache_discovery=False)
