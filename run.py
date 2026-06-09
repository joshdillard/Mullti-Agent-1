#!/usr/bin/env python3
"""Entrypoint for Mullti-Agent-1.

Usage:
    python run.py list
    python run.py status
    python run.py run daily_content_idea
    python run.py run research_topic_series --topic "AI b-roll workflows"
    python run.py serve
"""

import sys
from pathlib import Path

# Make `src/` importable without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from multiagent.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
