# Deployment

Two supported paths. Both run **two long-lived processes** on an always-on box:

- **scheduler** (`run.py serve`) — fires agents on their cron schedules
- **dashboard** (`run.py dashboard`) — the monitoring UI

They share the `state/` directory, so the dashboard shows runs the scheduler
performed (and vice-versa).

> **Why not gunicorn/multiple workers?** The dashboard keeps live-run state and
> the run buffer in memory and uses background threads. Run it as a **single
> process** (the built-in server) — that's the correct setup here, not a
> limitation. For a personal/team tool the traffic is tiny.

Pre-req either way: **set a dashboard password** so the UI isn't open to the
internet.

```bash
cp .env.example .env
# fill in ANTHROPIC_API_KEY etc., then:
#   DASHBOARD_PASSWORD=your-strong-password
#   DASHBOARD_SECRET=$(openssl rand -hex 32)
#   DASHBOARD_DOMAIN=agents.yourstudio.com    # for HTTPS via Caddy
```

---

## Option A — Docker Compose (recommended)

Brings up scheduler + dashboard + **Caddy** (auto-HTTPS) in one command.

```bash
# 1. Point a DNS A record for DASHBOARD_DOMAIN at this server (ports 80 + 443 open).
# 2. Configure .env (keys + DASHBOARD_PASSWORD + DASHBOARD_DOMAIN).
docker compose up -d --build

docker compose logs -f          # watch it run
docker compose ps               # health status
```

Then open `https://<DASHBOARD_DOMAIN>` — Caddy fetches a TLS cert automatically.

**Bake in live integrations** (Stripe, Google, Ayrshare SDK):

```bash
docker compose build --build-arg INSTALL_EXTRAS=1 && docker compose up -d
```

**Quick local test (no domain):** in `docker-compose.yml`, under `dashboard`,
swap `expose: ["8765"]` for `ports: ["8765:8765"]`, `docker compose up dashboard`,
and open `http://localhost:8765`.

**Updating:**

```bash
git pull && docker compose up -d --build
```

State and secrets live in bind-mounts (`./state`, `./credentials`, `.env`), so
they survive rebuilds.

---

## Option B — systemd + Caddy on the host

For a plain VPS without Docker.

```bash
# 1. Install to /opt and create a venv
sudo git clone <your-repo> /opt/Mullti-Agent-1
cd /opt/Mullti-Agent-1
sudo useradd -r -s /usr/sbin/nologin multiagent
sudo python3 -m venv .venv
sudo .venv/bin/pip install -r requirements-full.txt
sudo cp .env.example .env && sudo nano .env        # add your keys + password
sudo chown -R multiagent:multiagent /opt/Mullti-Agent-1

# 2. Install the services
sudo cp deploy/multiagent-scheduler.service /etc/systemd/system/
sudo cp deploy/multiagent-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now multiagent-scheduler multiagent-dashboard

# 3. Front the dashboard with Caddy for HTTPS
sudo apt install -y caddy
sudo cp deploy/Caddyfile.systemd /etc/caddy/Caddyfile
sudo nano /etc/caddy/Caddyfile      # set your real domain
sudo systemctl reload caddy
```

Check status / logs:

```bash
systemctl status multiagent-scheduler multiagent-dashboard
journalctl -u multiagent-scheduler -f
```

The dashboard binds to `127.0.0.1:8765`; only Caddy is exposed publicly.

---

## Sanity checklist

- [ ] `DASHBOARD_PASSWORD` set (UI requires login)
- [ ] `https://<domain>/healthz` returns `{"ok": true}`
- [ ] `python run.py status` (or the dashboard pills) shows your live integrations
- [ ] Click **Test delivery** → Telegram message arrives
- [ ] **Run now** on an agent streams output
- [ ] Scheduler timezone in `config/agents.yaml` matches yours
