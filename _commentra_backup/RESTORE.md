# Commentra — backup bundle

This folder contains a **git bundle** of the full Commentra project (the
comment-mining board app: paste a social post URL → filter comments into
cards → generate content scripts). It was built in a Claude Code session but
could not be pushed to `github.com/joshdillard/commentra` directly because that
repo was not in the session's allowed scope.

The bundle (`commentra.bundle`) contains the **complete git history**, including
commit `67b10c2` with the entire app. `node_modules` is **not** included
(it's reinstalled with `npm install`).

## Restore it and push to the real repo

From your Mac (or any machine with git + GitHub access):

```bash
# 1. Clone the project out of the bundle
git clone /path/to/_commentra_backup/commentra.bundle commentra
cd commentra

# 2. Point it at your GitHub repo and push
git remote set-url origin https://github.com/joshdillard/commentra.git
git push -u origin main          # use a Personal Access Token as the password

# 3. Install deps and run
npm install
cp .env.example .env             # optional: add API keys
npx prisma migrate dev           # creates the local SQLite database
npm run dev                      # http://localhost:3000
```

If you don't have the bundle file locally, you can pull it from this repo:
it lives at `_commentra_backup/commentra.bundle` on branch
`claude/sharp-dirac-71b8qw`.

## What's inside

- **Next.js + TypeScript + Tailwind**, dnd-kit board, Prisma/SQLite sessions.
- Pluggable platform fetchers: live YouTube (Data API v3), realistic demo data
  for X/LinkedIn/Facebook/Instagram.
- Claude-powered comment filtering + script writing, with a zero-config
  heuristic fallback so it runs with **no API keys**.
- See the project's own `README.md` (inside the bundle) for full docs.
