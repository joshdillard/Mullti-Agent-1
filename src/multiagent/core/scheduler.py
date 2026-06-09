"""Cron scheduler that runs enabled agents on their configured schedules.

Backed by APScheduler. `schedule: manual` agents are skipped here — invoke
them directly via the CLI. This process is what you'd run under systemd or
`nohup` on an always-on box; alternatively, drop each agent into the OS
crontab using `python run.py run <agent>` (see README).
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from .agent import Agent
from .registry import load_all
from .runner import run_agent
from ..settings import Settings

log = logging.getLogger("multiagent.scheduler")


def _run_agent(agent_cls: type[Agent], settings: Settings) -> None:
    run_agent(agent_cls.name, settings)


def build_scheduler(settings: Settings) -> BlockingScheduler:
    registry = load_all()
    sched = BlockingScheduler(timezone=settings.timezone)

    scheduled = 0
    for name, agent_cls in registry.items():
        cfg = settings.agent_config(name)
        if not cfg.get("enabled", False):
            log.info("skip %s (disabled)", name)
            continue
        schedule = cfg.get("schedule", "manual")
        if schedule == "manual":
            log.info("skip %s (manual)", name)
            continue
        sched.add_job(
            _run_agent,
            trigger=CronTrigger.from_crontab(schedule, timezone=settings.timezone),
            args=[agent_cls, settings],
            id=name,
            name=name,
            misfire_grace_time=3600,
            coalesce=True,
        )
        scheduled += 1
        log.info("scheduled %s @ '%s'", name, schedule)

    log.info("%d agent(s) scheduled", scheduled)
    return sched
