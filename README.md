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

# 4. Open the monitoring dashboard
python run.py dashboard        # http://127.0.0.1:8765

# 5. Add your keys
cp .env.example .env          # then fill in ANTHROPIC_API_KEY at minimum
```

---

## Monitoring dashboard

```bash
python run.py dashboard        # → http://127.0.0.1:8765
```

A single-page board to check on everything daily:

- **Agent grid** — every agent with its schedule, next run, last-run status
  (green/red/spinner), delivery targets, and a preview of its latest output.
- **Run now** — trigger any agent on the spot (runs in the background); click
  **View output** to read the full result.
- **Recent activity** feed — the last 40 runs across all agents.
- **Integration pills** — at a glance, which services are `live` vs `demo`.
- Auto-refreshes every 12s.

Run it alongside `python run.py serve` (the scheduler) on the same box.

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
│   ├── runner.py           # shared run path (scheduler/CLI/dashboard)
│   ├── scheduler.py        # APScheduler cron runner
│   ├── history.py          # run-history store (what the dashboard reads)
│   └── state.py            # per-agent JSON memory (dedupe ideas, leads, etc.)
├── integrations/           # one adapter per service, each with demo fallback
│   ├── ayrshare.py         # unified TikTok + LinkedIn provider
│   ├── tiktok.py  linkedin.py  gmail.py  gsheets.py
│   ├── gdocs.py   stripe_client.py  telegram.py  websearch.py
├── dashboard/              # Flask monitoring UI (app.py + templates/)
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

## Connecting TikTok & LinkedIn

The two hardest integrations don't hand out simple API keys — they require
developer-app review and OAuth. The fastest path is a **third-party aggregator**
that has already done that work. After comparing the options:

| Provider | Posts | Analytics/Audience | TikTok | LinkedIn | Best for |
|---|---|---|---|---|---|
| **[Ayrshare](https://www.ayrshare.com)** ⭐ | ✅ | ✅ | ✅ | ✅ | One key for posting **and** analytics — built in here |
| [Phyllo](https://www.getphyllo.com) | ❌ | ✅✅ | ✅ | ✅ | Deep audience demographics (read-only) |
| [Upload-Post](https://www.upload-post.com) | ✅ | limited | ✅ | ✅ | Cheapest; free tier; ships an MCP server |
| Official APIs | ✅ | ✅ | app review | app review | Free but slow to approve |
| [`davidteather/TikTok-Api`](https://github.com/davidteather/TikTok-Api) (6.4k★) | ❌ | scrape trends | ✅ | — | Trend data (unofficial; ToS risk) |

**Ayrshare is wired in.** Set `AYRSHARE_API_KEY` in `.env`, connect your TikTok +
LinkedIn accounts in their dashboard, and the TikTok/LinkedIn adapters route
through it automatically — no code changes. Posting stays a **dry-run** (composed
but not published) until you set `AYRSHARE_AUTO_POST=true`, so nothing goes out
to your audience by accident. Trend discovery (`spot_viral_opportunities`) and
brand/competitor research run on Claude's built-in web search, so they need no
social key at all.

> Want richer follower demographics for `research_audience` /
> `weekly_performance_review`? Add Phyllo as a second provider — the adapter
> seam is the same as Ayrshare's.

## Taking an integration live

Add the key to `.env` and the agent flips from demo to live automatically.
Suggested order:

1. **`ANTHROPIC_API_KEY`** — makes all reasoning real.
2. **Telegram** — `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` (fully implemented —
   phone alerts work immediately).
3. **Ayrshare** — `AYRSHARE_API_KEY` → TikTok + LinkedIn posting & analytics.
4. **Stripe** — `STRIPE_API_KEY` (revenue summary + tax prep are live-ready).
5. **Google** (Gmail/Sheets/Docs) — drop OAuth `client_secret.json` at
   `GOOGLE_CREDENTIALS_FILE`; `pip install google-api-python-client google-auth-oauthlib`.

---

## Tests

```bash
python -m pytest tests/ -q
```

Smoke tests verify every agent registers, integrations fall back to demo mode
cleanly, and config loads — all without any API keys.
