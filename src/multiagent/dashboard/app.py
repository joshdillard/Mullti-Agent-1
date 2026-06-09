"""Flask monitoring dashboard.

  python run.py dashboard            # http://127.0.0.1:8765

Features:
  - Agent grid: schedule, next/last run, status, latest output
  - "Next 24 hours" timeline of upcoming scheduled runs
  - Run now: runs in a background thread and streams live output
  - Test delivery: sends a real Telegram ping to confirm the channel
  - Recent activity feed + integration live/demo pills
  - Optional password gate (DASHBOARD_PASSWORD) before hosting on a VPS
"""

from __future__ import annotations

import hmac
import logging
import os
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.triggers.cron import CronTrigger
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ..core import History, load_all, run_agent
from ..integrations import Integrations
from ..settings import Settings

log = logging.getLogger("multiagent.dashboard")

# Agents currently executing, and a live-output buffer per agent.
_RUNNING: set[str] = set()
_LIVE: dict[str, dict] = {}
_LOCK = threading.Lock()
_LIVE_CAP = 20000  # keep the tail of long generations


# --- schedule helpers -------------------------------------------------------
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
                {"agent": name, "description": cls.description, "when": fire.isoformat(timespec="minutes")}
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
                "last": latest.get(name),
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


# --- background run with live streaming -------------------------------------
def _make_sink(name: str):
    def sink(delta: str) -> None:
        with _LOCK:
            buf = _LIVE.get(name)
            if buf is not None:
                buf["text"] = (buf["text"] + delta)[-_LIVE_CAP:]
    return sink


def _run_in_background(name: str, settings: Settings) -> None:
    def task() -> None:
        title = ""
        try:
            result = run_agent(name, settings, live_sink=_make_sink(name))
            title = result.title
        except Exception:  # noqa: BLE001
            log.exception("background run of %s failed", name)
            title = "Run failed — check logs"
        finally:
            with _LOCK:
                _RUNNING.discard(name)
                if name in _LIVE:
                    _LIVE[name]["done"] = True
                    _LIVE[name]["title"] = title

    with _LOCK:
        if name in _RUNNING:
            return
        _RUNNING.add(name)
        _LIVE[name] = {"text": "", "done": False, "title": ""}
    threading.Thread(target=task, name=f"run-{name}", daemon=True).start()


# --- app --------------------------------------------------------------------
def create_app(settings: Settings) -> Flask:
    app = Flask(__name__)
    password = os.getenv("DASHBOARD_PASSWORD", "")
    app.secret_key = os.getenv("DASHBOARD_SECRET") or os.urandom(24)

    @app.before_request
    def _guard():
        if not password:
            return None  # open mode (local dev)
        if request.endpoint in ("login", "static", "healthz"):
            return None
        if session.get("authed"):
            return None
        if request.path.startswith("/api/"):
            return jsonify({"error": "auth required"}), 401
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if not password:
            return redirect(url_for("index"))
        error = ""
        if request.method == "POST":
            if hmac.compare_digest(request.form.get("password", ""), password):
                session["authed"] = True
                return redirect(url_for("index"))
            error = "Incorrect password."
        return render_template("login.html", error=error, business=settings.business.name)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/healthz")
    def healthz():
        return jsonify({"ok": True})

    @app.route("/")
    def index():
        return render_template(
            "index.html", business=settings.business.name, auth_enabled=bool(password)
        )

    @app.route("/api/state")
    def state():
        return jsonify(build_state(settings))

    @app.route("/api/run/<name>", methods=["POST"])
    def run(name: str):
        if name not in load_all():
            return jsonify({"error": "unknown agent"}), 404
        _run_in_background(name, settings)
        return jsonify({"started": True, "agent": name})

    @app.route("/api/run-output/<name>")
    def run_output(name: str):
        with _LOCK:
            buf = _LIVE.get(name)
            data = dict(buf) if buf else {"text": "", "done": True, "title": ""}
        return jsonify(data)

    @app.route("/api/test-delivery", methods=["POST"])
    def test_delivery():
        ix = Integrations()
        msg = f"✅ Test from your {settings.business.name} agent dashboard — delivery is working."
        sent = ix.telegram.send(msg)
        return jsonify({"sent": bool(sent), "configured": ix.telegram.configured})

    return app


def run_dashboard(settings: Settings, host: str = "127.0.0.1", port: int = 8765) -> None:
    app = create_app(settings)
    if not os.getenv("DASHBOARD_PASSWORD") and host not in ("127.0.0.1", "localhost"):
        print(
            "\n  ⚠️  No DASHBOARD_PASSWORD set but binding to a public host.\n"
            "      Set DASHBOARD_PASSWORD in .env before exposing this.\n"
        )
    print(f"\n  Dashboard → http://{host}:{port}\n")
    app.run(host=host, port=port, debug=False)
