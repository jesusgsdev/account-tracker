# FolioTrack — UK Financial Account Tracker

A **local-first** web application for tracking UK financial accounts (ISAs, SIPPs, LISAs, GIAs, and more) with a complete audit log and portfolio charts.

## Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3 + Vite + TypeScript |
| Backend | FastAPI (Python 3.11+) |
| Database | SQLite (`backend/tracker.db`) |
| Charts | Chart.js via vue-chartjs |

## Quick Start

```bash
./start.sh
```

Then open **http://localhost:5173**

> The `tracker.db` file is created automatically in `backend/`. To back up your data, just copy that file.

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

- 📊 **Dashboard** — Net worth hero card, category breakdown, area chart (1M/3M/6M/1Y/All), allocation donut
- 🏦 **Accounts** — Grouped by Investments / Retirement / Savings, add/edit/delete with UK account types
- 📋 **Audit Log** — Every value change recorded with delta and %, filter by account, export CSV
- 📈 **Charts** — Net worth over time + per-account history
- 📱 **Responsive** — Full mobile support with bottom navigation

## UK Account Types Supported

Stocks & Shares ISA, Cash ISA, LISA (Lifetime ISA), SIPP, Workplace Pension, GIA, Premium Bonds, Fixed-Term Bond, Current Account, Savings Account, and more.

## Database, Backup & Restore

The SQLite database lives at `backend/tracker.db`. You can:
- Open it with [DB Browser for SQLite](https://sqlitebrowser.org/)
- Copy/move the `tracker.db` file to back up your data
- Inspect the tables (`accounts`, `audit_log`, `properties`, `mortgage_parts`, etc.) directly

### JSON Backup & Restore

A JSON utility script is provided in the `backend/` folder to backup all tables to a portable JSON file, which is highly useful when database schema upgrades require rebuilding the SQLite file:

```bash
# Navigate and activate backend virtual env
cd backend
source venv/bin/activate

# 1. Back up database tables to backup.json
./backup.py --backup backup.json

# 2. Restore database tables from backup.json (clears current data first)
./backup.py --restore backup.json
```

## API Docs

When the backend is running, visit **http://localhost:8000/docs** for the interactive Swagger UI.
