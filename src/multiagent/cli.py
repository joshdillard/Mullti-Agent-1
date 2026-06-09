"""Command-line interface.

  python run.py list                 # show all agents, schedules, status
  python run.py status               # show which integrations are live
  python run.py run <agent> [opts]   # run one agent now
  python run.py serve                # start the cron scheduler (long-running)

Run options:
  --topic "..."     pass a topic (e.g. research_topic_series)
  --query "..."     pass a query (e.g. find_next_role)
  --set key=value   pass any other runtime param
"""

from __future__ import annotations

import argparse
import logging
import sys

from .core import load_all, run_agent
from .settings import Settings


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_list(settings: Settings) -> int:
    registry = load_all()
    print(f"\n{len(registry)} agents:\n")
    for name in sorted(registry):
        cfg = settings.agent_config(name)
        enabled = "on " if cfg.get("enabled", False) else "off"
        schedule = cfg.get("schedule", "manual")
        dests = ",".join(cfg.get("deliver_to", [])) or "-"
        desc = registry[name].description
        print(f"  [{enabled}] {name:28s} {schedule:16s} → {dests:22s} {desc}")
    print()
    return 0


def cmd_status(settings: Settings) -> int:
    from .integrations import Integrations

    ix = Integrations()
    print("\nIntegration status (live = key present, demo = sample data):\n")
    for name, live in sorted(ix.status().items()):
        print(f"  {name:12s} {'LIVE' if live else 'demo'}")
    print(f"\n  model: {settings.model}")
    print(f"  business: {settings.business.name} ({settings.business.niche})\n")
    return 0


def cmd_run(settings: Settings, name: str, params: dict) -> int:
    if name not in load_all():
        print(f"unknown agent '{name}'. Try `list`.", file=sys.stderr)
        return 2
    result = run_agent(name, settings, params=params)
    return 0 if result.ok else 1


def cmd_dashboard(settings: Settings, host: str, port: int) -> int:
    from .dashboard.app import run_dashboard

    run_dashboard(settings, host=host, port=port)
    return 0


def cmd_serve(settings: Settings) -> int:
    from .core.scheduler import build_scheduler

    sched = build_scheduler(settings)
    print("Scheduler running. Ctrl-C to stop.")
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nstopped.")
    return 0


def _parse_params(args: argparse.Namespace) -> dict:
    params: dict[str, str] = {}
    if args.topic:
        params["topic"] = args.topic
    if args.query:
        params["query"] = args.query
    for item in args.set or []:
        if "=" in item:
            k, v = item.split("=", 1)
            params[k.strip()] = v.strip()
    return params


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="multiagent", description=__doc__)
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list all agents")
    sub.add_parser("status", help="show integration status")
    sub.add_parser("serve", help="start the cron scheduler")

    p_run = sub.add_parser("run", help="run one agent now")
    p_run.add_argument("agent")
    p_run.add_argument("--topic")
    p_run.add_argument("--query")
    p_run.add_argument("--set", action="append", metavar="key=value")

    p_dash = sub.add_parser("dashboard", help="launch the monitoring dashboard")
    p_dash.add_argument("--host", default="127.0.0.1")
    p_dash.add_argument("--port", type=int, default=8765)

    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    settings = Settings.load()

    if args.command == "list":
        return cmd_list(settings)
    if args.command == "status":
        return cmd_status(settings)
    if args.command == "serve":
        return cmd_serve(settings)
    if args.command == "run":
        return cmd_run(settings, args.agent, _parse_params(args))
    if args.command == "dashboard":
        return cmd_dashboard(settings, args.host, args.port)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
