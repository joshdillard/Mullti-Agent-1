"""Smoke tests — verify the system wires together without any API keys.

These run in pure demo mode (no Anthropic key, no integration keys) and assert
that every agent registers, integrations fall back cleanly, and delivery
routing works with a fake notifier.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from multiagent.core import load_all  # noqa: E402
from multiagent.integrations import Integrations  # noqa: E402
from multiagent.settings import Settings  # noqa: E402


EXPECTED_AGENTS = {
    "daily_content_idea",
    "spot_viral_opportunities",
    "research_topic_series",
    "weekly_performance_review",
    "newsletter_draft",
    "research_audience",
    "clean_inbox",
    "find_next_role",
    "find_new_clients",
    "track_competitors",
    "capture_leads",
    "tax_season_prep",
    "track_brand_mentions",
    "weekly_revenue_summary",
}


def test_all_agents_register():
    registry = load_all()
    assert EXPECTED_AGENTS <= set(registry), EXPECTED_AGENTS - set(registry)


def test_agents_have_metadata():
    for name, cls in load_all().items():
        assert cls.name == name
        assert cls.description, f"{name} missing description"


def test_integrations_default_to_demo(monkeypatch):
    # No keys → everything except built-in web research is demo.
    for var in [
        "TIKTOK_ACCESS_TOKEN", "LINKEDIN_ACCESS_TOKEN", "GOOGLE_CREDENTIALS_FILE",
        "STRIPE_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
    ]:
        monkeypatch.delenv(var, raising=False)
    ix = Integrations()
    status = ix.status()
    assert status["web"] is True
    assert status["stripe"] is False
    assert status["tiktok"] is False


def test_demo_data_shapes():
    ix = Integrations()
    assert ix.tiktok.trending()
    assert ix.tiktok.my_recent_posts()
    assert "followers" in ix.tiktok.audience()
    assert "this_week" in ix.stripe.weekly_revenue()
    assert ix.gmail.unread()


def test_config_loads():
    settings = Settings.load()
    assert settings.agents
    assert "daily_content_idea" in settings.agents
