# Mullti-Agent-1

A multi-agent automation system for a **video production & AI content** business.
Each automation ("agent") has a schedule, reads from the tools you already use
(TikTok, LinkedIn, Gmail, Sheets, Docs, Stripe), thinks with Claude
(`claude-opus-4-8`), and delivers results where you want them (Telegram, Google
Docs, Sheets, Gmail drafts).

It runs **today** with zero setup — every integration falls back to realistic
demo data until you add its API key, so you can see the whole thing work before
wiring anything live.

---

## The 14 agents

| Agent | Schedule | Reads | Delivers |
|---|---|---|---|
| `daily_content_idea` | daily 8am | TikTok trends + your posts | Telegram + LinkedIn draft |
| `spot_viral_opportunities` | 3×/day | TikTok niche trends | Telegram |
| `research_topic_series` | manual | Web research | Google Doc (5-part series) |
| `weekly_performance_review` | Mon 9am | TikTok analytics | Telegram + Sheet |
| `newsletter_draft` | Fri 3pm | Your week's posts | Google Doc |
| `research_audience` | manual | TikTok audience | Telegram |
| `clean_inbox` | daily 7:30am | Gmail | Telegram + Gmail drafts |
| `find_next_role` | manual *(off)* | LinkedIn jobs | Telegram |
| `find_new_clients` | nightly 2am | LinkedIn + web | Telegram + Gmail drafts |
| `track_competitors` | Mon 8am | Web + LinkedIn | Telegram |
| `capture_leads` | daily 7am | Gmail | Sheet + Gmail drafts |
| `tax_season_prep` | quarterly | Stripe | Sheet |
| `track_brand_mentions` | daily 6pm | Web + TikTok | Telegram |
| `weekly_revenue_summary` | Mon 8am | Stripe | Telegram |

Schedules and destinations live in [`config/agents.yaml`](config/agents.yaml) —
edit them there, no code changes needed.

---

## Quick start

```bash
# 1. Install
pip install -r requirements.txt

# 2. See the agents and their status
python run.py list
python run.py status          # shows which integrations are LIVE vs demo

# 3. Run one now (works in demo mode without any keys)
python run.py run weekly_revenue_summary
python run.py run research_topic_series --topic "AI b-roll workflows"

# 4. Add your keys
cp .env.example .env          # then fill in ANTHROPIC_API_KEY at minimum
```

The only key needed for the reasoning to be *real* (not stubbed) is
`ANTHROPIC_API_KEY`. Every other integration is optional and activates the
moment its key is present.

---

## Running on a schedule (local / cron)

Two equivalent options — pick one:

**Option A — built-in scheduler** (one always-on process):

```bash
python run.py serve
```

Run it under `systemd`, `tmux`, `nohup`, or a cheap VPS. It fires each enabled,
non-`manual` agent on its cron schedule from `config/agents.yaml`.

**Option B — OS crontab** (one line per agent). Each agent is also a one-shot
command, so you can let the OS scheduler drive it:

```cron
# m h dom mon dow   command
0 8   * * *  cd /path/to/Mullti-Agent-1 && python run.py run daily_content_idea
0 8   * * 1  cd /path/to/Mullti-Agent-1 && python run.py run weekly_revenue_summary
0 7   * * *  cd /path/to/Mullti-Agent-1 && python run.py run capture_leads
```

---

## How it's built

```
run.py                      # entrypoint
config/agents.yaml          # schedules + per-agent settings
src/multiagent/
├── settings.py             # env + config loading, business context
├── llm.py                  # Claude wrapper (opus-4-8, adaptive thinking, streaming)
├── notify.py               # routes results to telegram/gdoc/sheet/gmail/linkedin
├── core/
│   ├── agent.py            # Agent base class + AgentResult
│   ├── context.py          # per-run context (llm, integrations, state, notify)
│   ├── registry.py         # @register + auto-discovery
│   ├── scheduler.py        # APScheduler cron runner
│   └── state.py            # per-agent JSON memory (dedupe ideas, leads, etc.)
├── integrations/           # one adapter per service, each with demo fallback
│   ├── tiktok.py  linkedin.py  gmail.py  gsheets.py
│   ├── gdocs.py   stripe_client.py  telegram.py  websearch.py
└── agents/                 # the 14 agents, one file each
```

**Design notes**

- **Demo-first.** Every adapter declares the env vars it needs. Missing keys →
  it returns representative sample data (clearly logged) instead of crashing, so
  the system is runnable and demoable before any integration is live.
- **Agents stay clean.** An agent reads data, asks Claude, and returns an
  `AgentResult`. It declares destinations in config; `notify.py` handles routing.
- **Memory between runs.** `state/` holds small JSON files so agents don't repeat
  content ideas, re-email the same leads, or lose last week's revenue snapshot.
- **Claude does the thinking.** `llm.py` defaults to `claude-opus-4-8` with
  adaptive thinking, streams long outputs, and exposes `complete_json()` for
  structured tasks (inbox triage, lead extraction). Web-research agents use
  Claude's built-in `web_search` tool — no extra search key required.

---

## Taking an integration live

Each adapter has a clearly marked `raise NotImplementedError(...)` at the live
call site with the exact API to wire. Add the key to `.env`, implement that one
method, and the agent flips from demo to live automatically. Suggested order:

1. **`ANTHROPIC_API_KEY`** — makes all reasoning real.
2. **Telegram** — `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` (already fully
   implemented — your phone alerts work immediately).
3. **Stripe** — `STRIPE_API_KEY` (revenue summary + tax prep are live-ready).
4. **Google** (Gmail/Sheets/Docs) — drop OAuth `client_secret.json` at
   `GOOGLE_CREDENTIALS_FILE`; `pip install google-api-python-client google-auth-oauthlib`.
5. **TikTok / LinkedIn** — require platform app review; structure + sample data
   are in place so downstream agents already produce real output.

---

## Tests

```bash
python -m pytest tests/ -q
```

Smoke tests verify every agent registers, integrations fall back to demo mode
cleanly, and config loads — all without any API keys.
