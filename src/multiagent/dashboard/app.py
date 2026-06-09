"""Flask monitoring dashboard.

  python run.py dashboard            # http://127.0.0.1:8765

Shows every agent's schedule, next/last run, status, and latest output; a
live activity feed; integration status; and a one-click "Run now" button
(runs the agent in a background thread). State is polled from /api/state.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.triggers.cron import CronTrigger
from flask import Flask, jsonify, render_template

from ..core import History, load_all, run_agent
from ..integrations import Integrations
from ..settings import Settings

log = logging.getLogger("multiagent.dashboard")

# Agents currently executing (so the UI can show a spinner + disable the button).
_RUNNING: set[str] = set()
_LOCK = threading.Lock()


def _next_run(schedule: str, tz: ZoneInfo) -> str | None:
    if not schedule or schedule == "manual":
        return None
    try:
        trigger = CronTrigger.from_crontab(schedule, timezone=tz)
        nxt = trigger.get_next_fire_time(None, datetime.now(tz))
        return nxt.isoformat(timespec="minutes") if nxt else None
    except (ValueError, TypeError):
        return None


def upcoming_runs(settings: Settings, hours: int = 24) -> list[dict]:
    """Every scheduled fire across all enabled agents over the next `hours`."""
    tz = ZoneInfo(settings.timezone)
    registry = load_all()
    now = datetime.now(tz)
    end = now + timedelta(hours=hours)
    events: list[dict] = []

    for name, cls in registry.items():
        cfg = settings.agent_config(name)
        schedule = cfg.get("schedule", "manual")
        if not cfg.get("enabled") or schedule == "manual":
            continue
        try:
            trigger = CronTrigger.from_crontab(schedule, timezone=tz)
        except (ValueError, TypeError):
            continue
        fire = trigger.get_next_fire_time(None, now)
        while fire and fire <= end:
            events.append(
                {
                    "agent": name,
                    "description": cls.description,
                    "when": fire.isoformat(timespec="minutes"),
                }
            )
            fire = trigger.get_next_fire_time(fire, fire)

    events.sort(key=lambda e: e["when"])
    return events


def _humanize(schedule: str) -> str:
    table = {
        "0 8 * * *": "Daily · 8:00am",
        "30 7 * * *": "Daily · 7:30am",
        "0 7 * * *": "Daily · 7:00am",
        "0 18 * * *": "Daily · 6:00pm",
        "0 2 * * *": "Nightly · 2:00am",
        "0 7,12,17 * * *": "3×/day",
        "0 9 * * 1": "Mondays · 9:00am",
        "0 8 * * 1": "Mondays · 8:00am",
        "0 15 * * 5": "Fridays · 3:00pm",
        "0 9 1 1,4,7,10 *": "Quarterly",
    }
    if schedule == "manual":
        return "On-demand"
    return table.get(schedule, schedule)


def build_state(settings: Settings) -> dict:
    tz = ZoneInfo(settings.timezone)
    registry = load_all()
    history = History(settings.state_dir / "history.json")
    latest = history.latest_per_agent()

    agents = []
    for name in sorted(registry):
        cfg = settings.agent_config(name)
        schedule = cfg.get("schedule", "manual")
        last = latest.get(name)
        with _LOCK:
            running = name in _RUNNING
        agents.append(
            {
                "name": name,
                "description": registry[name].description,
                "enabled": cfg.get("enabled", False),
                "schedule": schedule,
                "schedule_human": _humanize(schedule),
                "deliver_to": cfg.get("deliver_to", []),
                "next_run": _next_run(schedule, tz) if cfg.get("enabled") else None,
                "running": running,
                "last": last,
            }
        )

    return {
        "business": {"name": settings.business.name, "niche": settings.business.niche},
        "model": settings.model,
        "integrations": Integrations().status(),
        "agents": agents,
        "timeline": upcoming_runs(settings, hours=24),
        "activity": history.all()[:40],
        "now": datetime.now(tz).isoformat(timespec="seconds"),
    }


def _run_in_background(name: str, settings: Settings) -> None:
    def task() -> None:
        try:
            run_agent(name, settings)
        except Exception:  # noqa: BLE001
            log.exception("background run of %s failed", name)
        finally:
            with _LOCK:
                _RUNNING.discard(name)

    with _LOCK:
        if name in _RUNNING:
            return
        _RUNNING.add(name)
    threading.Thread(target=task, name=f"run-{name}", daemon=True).start()


def create_app(settings: Settings) -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template("index.html", business=settings.business.name)

    @app.route("/api/state")
    def state():
        return jsonify(build_state(settings))

    @app.route("/api/run/<name>", methods=["POST"])
    def run(name: str):
        if name not in load_all():
            return jsonify({"error": "unknown agent"}), 404
        _run_in_background(name, settings)
        return jsonify({"started": True, "agent": name})

    return app


def run_dashboard(settings: Settings, host: str = "127.0.0.1", port: int = 8765) -> None:
    app = create_app(settings)
    print(f"\n  Dashboard → http://{host}:{port}\n")
    app.run(host=host, port=port, debug=False)
