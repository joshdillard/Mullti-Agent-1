# Setup walkthrough

Go live one integration at a time. Each step is independent — the system keeps
running in demo mode for anything you haven't set up yet. After each step, run
`python run.py status` to confirm it flipped from `demo` to `live`.

> All keys go in `.env` (copy it from `.env.example` first):
> ```bash
> cp .env.example .env
> ```

---

## Step 1 — Claude (the brain) · required

This is the only key that makes the agents *think* instead of returning stubs.

1. Go to **https://console.anthropic.com** → sign in.
2. **Settings → API Keys → Create Key**. Copy it (starts with `sk-ant-...`).
3. In `.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
4. While you're there, set your business context so output is on-brand:
   ```
   BUSINESS_NAME=Your Studio
   BUSINESS_NICHE=video production and AI content
   BUSINESS_HANDLE=@yourhandle
   ```
5. Verify:
   ```bash
   python run.py run weekly_revenue_summary
   ```
   You should see a real, written summary (not “stub output”).

---

## Step 2 — Telegram (where alerts land) · 5 minutes

Telegram is fully implemented — once these two values are set, your phone gets
the content ideas, trend alerts, and briefs.

### 2a. Create a bot and get the token

1. In Telegram, open a chat with **@BotFather**.
2. Send `/newbot`. Follow the prompts (give it a name + a username ending in
   `bot`, e.g. `mystudio_agents_bot`).
3. BotFather replies with a **token** like `8123456789:AAH...xyz`. Copy it.
   ```
   TELEGRAM_BOT_TOKEN=8123456789:AAH...xyz
   ```

### 2b. Get your chat ID

1. Open a chat with **your new bot** and send it any message (e.g. “hi”).
   *(A bot can’t message you until you’ve messaged it first.)*
2. In a browser, visit:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
   (paste your real token in place of `<YOUR_TOKEN>`).
3. Find `"chat":{"id":123456789,...}` in the JSON. That number is your chat ID.
   ```
   TELEGRAM_CHAT_ID=123456789
   ```

### 2c. Test

```bash
python run.py run daily_content_idea
```
A content idea should arrive in your Telegram chat.

> Tip: for a team, create a Telegram **group**, add the bot, and use the
> group’s (negative) chat ID instead.

---

## Step 3 — Zernio (posting + DMs + cold outreach) · recommended

Zernio is the primary social tool: it posts to 15 platforms **and** reads/replies
to DMs — it powers the `reply_to_dms` agent and your social posting + outreach.

1. Sign up at **https://zernio.com** (your first 2 connected accounts are free).
2. In the Zernio dashboard, **connect your social accounts** (TikTok, LinkedIn,
   Instagram, etc.) and authorize them.
3. Copy your **API key** (it starts with `sk_`) and add it to `.env`:
   ```
   ZERNIO_API_KEY=sk_...your-key...
   ```
4. **Safety — leave these OFF until you've reviewed what it produces.** By
   default Zernio *drafts* posts and DM replies but does **not** send them:
   ```
   ZERNIO_AUTO_POST=false      # set true to actually publish posts
   ZERNIO_AUTO_SEND=false      # set true to actually send DM replies / outreach
   ```
5. Test:
   ```bash
   python run.py status            # zernio should read "LIVE"
   python run.py run reply_to_dms  # drafts replies to your unread DMs
   ```

What this unlocks: real social posting (`daily_content_idea`'s LinkedIn post),
the `reply_to_dms` agent (auto-drafts replies to DMs across platforms), and DM
cold outreach. Flip the two safety flags to `true` only when you trust the drafts.

> Prefer Ayrshare instead, or want it as a backup? It's still supported —
> see the optional step below.

## Step 3b — Ayrshare (alternative to Zernio) · optional

Ayrshare is the shortcut around TikTok/LinkedIn app review. One key gives the
agents both **posting** and **analytics** on both platforms.

1. Sign up at **https://www.ayrshare.com** (the free tier is enough to start;
   posting *video* to TikTok needs a paid plan, but analytics + drafting work
   on free).
2. In the Ayrshare dashboard, **connect your social accounts**: click
   **Connect** on **TikTok** and **LinkedIn** and authorize them.
3. Go to **API Key** in the dashboard and copy your key.
   ```
   AYRSHARE_API_KEY=your-ayrshare-key
   ```
4. **Safety setting.** By default the system *drafts* posts but does **not**
   publish them — you’ll see `DRY-RUN` in the logs. Leave this off until you’ve
   reviewed a few drafts:
   ```
   AYRSHARE_AUTO_POST=false      # set to true only when you're ready to auto-post
   ```
5. Test:
   ```bash
   python run.py status                       # ayrshare should read "LIVE"
   python run.py run weekly_performance_review # now uses your real TikTok numbers
   python run.py run daily_content_idea        # LinkedIn variant is staged via Ayrshare
   ```

What this unlocks: real TikTok analytics for `weekly_performance_review` and
`research_audience`, and real LinkedIn drafting for `daily_content_idea` and
`find_new_clients`.

> Trend discovery (`spot_viral_opportunities`) and brand/competitor research
> run on Claude’s built-in web search — no social key needed for those.

---

## Step 4 — Stripe (revenue + tax) · optional

1. **https://dashboard.stripe.com** → **Developers → API keys**.
2. Copy your **Secret key** (`sk_live_...`, or `sk_test_...` to try it safely).
   ```
   STRIPE_API_KEY=sk_live_...
   ```
3. `pip install stripe`, then test:
   ```bash
   python run.py run weekly_revenue_summary
   ```

---

## Step 5 — Google (Gmail / Sheets / Docs) · optional

1. **https://console.cloud.google.com** → create/select a project.
2. **APIs & Services → Enable APIs**: enable **Gmail**, **Sheets**, **Docs**,
   and **Drive** APIs.
3. **Credentials → Create Credentials → OAuth client ID → Desktop app**.
   Download the JSON.
4. Save it as `credentials/google.json` (matches `GOOGLE_CREDENTIALS_FILE`).
5. Install libs and run any Google agent once — it opens a browser to authorize
   and caches a token:
   ```bash
   pip install google-api-python-client google-auth-oauthlib
   python run.py run clean_inbox
   ```
6. Optional: paste the spreadsheet IDs you want agents to write to:
   ```
   LEADS_SHEET_ID=...
   PERFORMANCE_SHEET_ID=...
   TAX_SHEET_ID=...
   ```
   (A sheet ID is the long string in its URL: `docs.google.com/spreadsheets/d/<ID>/edit`.)

---

## Step 6 — Phyllo (richer audience data) · optional

Adds detailed follower demographics for `research_audience` and
`weekly_performance_review`.

1. Sign up at **https://www.getphyllo.com** and create an app to get a
   **Client ID** and **Secret**.
2. Connect your TikTok account through Phyllo and note the **account ID**.
   ```
   PHYLLO_CLIENT_ID=...
   PHYLLO_SECRET=...
   PHYLLO_ACCOUNT_ID=...
   PHYLLO_ENV=sandbox        # switch to "production" when ready
   ```
3. Test:
   ```bash
   python run.py run research_audience
   ```

When Phyllo is configured it takes priority over Ayrshare for audience
demographics (it goes deeper); everything else is unchanged.

---

## Run it for real

```bash
python run.py serve        # cron scheduler (one always-on process)
python run.py dashboard    # monitoring UI at http://127.0.0.1:8765
```

Run both on a small always-on box (a $5 VPS, a Raspberry Pi, or a home server).
See the README for the systemd / crontab options.
