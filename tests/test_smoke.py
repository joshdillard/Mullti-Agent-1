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


def test_ayrshare_present_and_dry_run(monkeypatch):
    from multiagent.integrations.ayrshare import Ayrshare

    ix = Integrations()
    assert "ayrshare" in ix.status()

    # With a key but auto-post off, posting must be a dry run (never publishes).
    monkeypatch.setenv("AYRSHARE_API_KEY", "test-key")
    monkeypatch.delenv("AYRSHARE_AUTO_POST", raising=False)
    out = Ayrshare().post("hello", ["linkedin"])
    assert out["status"] == "dry_run"


def test_runner_records_history(tmp_path, monkeypatch):
    # Stub the LLM so no API key is needed.
    from multiagent import llm

    monkeypatch.setattr(llm.LLM, "complete", lambda self, p, **k: "stub output")
    monkeypatch.setattr(
        llm.LLM, "complete_json", lambda self, p, s, **k: {"leads": []}
    )

    from multiagent.core import run_agent, History
    from multiagent.dashboard.app import build_state

    settings = Settings.load()
    settings.state_dir = tmp_path
    result = run_agent("weekly_revenue_summary", settings)
    assert result.ok

    hist = History(tmp_path / "history.json").latest_per_agent()
    assert "weekly_revenue_summary" in hist

    state = build_state(settings)
    assert state["agents"]
    assert any(a["name"] == "weekly_revenue_summary" for a in state["agents"])
    assert "ayrshare" in state["integrations"]
    assert "phyllo" in state["integrations"]
    assert "timeline" in state


def test_timeline_lists_upcoming_runs():
    from multiagent.dashboard.app import upcoming_runs

    settings = Settings.load()
    events = upcoming_runs(settings, hours=24)
    # At least the daily agents should fire in any 24h window.
    assert events
    assert all({"agent", "description", "when"} <= set(e) for e in events)
    # Sorted ascending by time.
    times = [e["when"] for e in events]
    assert times == sorted(times)


def test_phyllo_preferred_for_audience(monkeypatch):
    monkeypatch.setenv("PHYLLO_CLIENT_ID", "id")
    monkeypatch.setenv("PHYLLO_SECRET", "secret")
    monkeypatch.setenv("PHYLLO_ACCOUNT_ID", "acct")
    from multiagent.integrations.phyllo import Phyllo

    # Force the live path to return mapped data; TikTok.audience should use it.
    monkeypatch.setattr(
        Phyllo, "audience", lambda self, account_id=None: {"followers": 99, "_source": "phyllo"}
    )
    from multiagent.integrations.tiktok import TikTok

    aud = TikTok().audience()
    assert aud.get("_source") == "phyllo"
