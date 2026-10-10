# FolioTrack — UK Financial Account Tracker

[![CI](https://github.com/jesusgsdev/account-tracker/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/jesusgsdev/account-tracker/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Vue 3](https://img.shields.io/badge/Vue-3-4FC08D?logo=vuedotjs&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-6-3178C6?logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)

A **local-first** web application for tracking UK financial accounts (ISAs, SIPPs, LISAs, GIAs, and more) with a complete audit log and portfolio charts.

## Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3 + Vite + TypeScript |
| Backend | FastAPI (Python 3.11+) |
| Database | SQLite (`backend/tracker.db`, or `$DB_PATH`) |
| Charts | Chart.js via vue-chartjs |

## Quick Start

```bash
./start.sh
```

Then open **http://localhost:5173**

> The `tracker.db` file is created automatically in `backend/`. `start.sh` binds the backend to 127.0.0.1; use `HOST=0.0.0.0 ./start.sh` to expose it on your network.

## Manual Start

```bash
# Terminal 1 — Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

## Features

- **Accounts and net worth** — ISAs, SIPPs, LISAs, GIAs, savings and more, grouped by Investments / Retirement / Savings, with a net worth hero card, category breakdown and allocation donut
- **Share holdings** — live prices (Yahoo Finance), non-GBP holdings converted to GBP, and automatic daily revaluation
- **Property and mortgages** — property values and mortgage parts, with equity counted in net worth
- **Dashboard history** — net worth and per-account charts (1M/3M/6M/1Y/All) reconstructed from the audit log
- **Audit log** — every value change recorded with delta and %, filterable by account
- **Wealth forecast** — long-term projection including state pension and net income estimate, with settings saved in the database
- **Daily snapshots and backups** — scheduled jobs with startup catch-up and retention
- **Single-user auth** — password-protected sessions, local-first data
- **Mobile friendly** — responsive layout with bottom navigation
- **CSV and JSON export** — accounts, audit log, properties and full backups

## UK Account Types Supported

Stocks & Shares ISA, Cash ISA, LISA (Lifetime ISA), SIPP, Workplace Pension, GIA, Premium Bonds, Fixed-Term Bond, Current Account, Savings Account, and more.

## Configuration

Environment variables (for Docker put them in `.env`, see `.env.example`):

| Variable | Purpose |
|---|---|
| `DB_PATH` | SQLite file location. Default `backend/tracker.db`; the container uses `/data/tracker.db`. |
| `AUTH_USERNAME` | Login username. |
| `AUTH_PASSWORD_HASH` | Password hash, generated with `python backend/hash_password.py`. |
| `SESSION_SECRET` | Long random string used to sign sessions. |
| `CORS_ORIGINS` | Comma-separated allowed origins (only if UI is on another origin). |
| `APP_UID` / `APP_GID` | Container user ids (default 1000); match the owner of `./data` if needed. |

### Auth setup

```bash
cp .env.example .env
cd backend && source venv/bin/activate
python hash_password.py            # prints a hash to paste into AUTH_PASSWORD_HASH
python -c "import secrets; print(secrets.token_urlsafe(48))"   # SESSION_SECRET
```

## Docker Deployment (e.g. Synology NAS)

```bash
cp .env.example .env     # fill in auth values (see above)
mkdir -p data            # database directory, mounted at /data in the container
docker compose up -d --build
```

The UI is served on port 8080. The backend runs as a non-root user (uid/gid 1000
by default) and has a healthcheck on `/api/health`; the frontend waits for it.
If the container cannot write to `./data`, either `chown -R 1000:1000 data`
or set `APP_UID`/`APP_GID` in `.env` to the owner of `data` and rebuild.

## Database, Backup & Restore

The SQLite database lives at `backend/tracker.db` locally (or `$DB_PATH`; `./data/tracker.db` in Docker). You can:
- Open it with [DB Browser for SQLite](https://sqlitebrowser.org/)
- Stop the app and copy `tracker.db` (plus `-wal`/`-shm` if present) to back up your data

### JSON Backup & Restore

`backend/backup.py` exports all tables (accounts, audit log, share holdings, properties, mortgage parts and their audit logs) to portable JSON, preserving ids:

```bash
cd backend && source venv/bin/activate

./backup.py --backup                       # writes backup-YYYYMMDD-HHMMSS.json
./backup.py --backup my.json --db /path/to/tracker.db
./backup.py --restore my.json              # replaces current data
```

Backups are written atomically. Restore validates the whole file first and then
replaces the data in a single transaction; on any error nothing is changed and
the exit code is non-zero. In Docker:
`docker compose exec backend python backup.py --backup /data/backup.json`.

### Automatic backups, snapshots and CSV export

The backend runs two daily background jobs (disabled with `*_ENABLED=0`):

- **Backups**: a dated `backup-YYYYMMDD-HHMMSS.json` (same format as `backup.py`) is written atomically to
  `BACKUP_DIR` (default: `backups/` next to the database, i.e. `./data/backups` in Docker) at `BACKUP_HOUR_UTC`
  (default 3). Only the newest `BACKUP_KEEP` (default 14) files matching that name pattern are kept. A catch-up
  backup runs on startup if the newest one is older than 24h.
  Restore from one: `docker compose exec backend python backup.py --restore /data/backups/backup-YYYYMMDD-HHMMSS.json`.
- **Snapshots**: at `SNAPSHOT_HOUR_UTC` (default 21) every active account with share holdings is revalued at live
  prices and an audit row noted `[auto-snapshot] ...` is written if the value moved by more than 0.005 GBP, so net-worth
  history keeps moving without manual edits. An account is skipped if any holding has no usable price or FX rate.
  A catch-up run happens on startup if the last snapshot is older than 24h.

Authenticated endpoints: `GET /api/snapshots/status`, `POST /api/snapshots/run` (409 if already running),
`GET /api/export/accounts.csv`, `audit.csv` (`?account_id=`), `properties.csv`, `backup.json` (download),
`GET /api/export/backups`, `POST /api/export/backups/run`. CSV text cells beginning with `= + - @` are prefixed with `'`
to prevent spreadsheet formula injection; numeric columns are left untouched.

## Tests

```bash
cd backend
source venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

Tests use a temporary SQLite file (via `DB_PATH`), never your real database.

## API Docs

When the backend is running, visit **http://localhost:8000/docs** for the interactive Swagger UI.
