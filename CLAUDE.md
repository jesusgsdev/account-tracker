# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

FolioTrack: a local-first, single-user UK financial account tracker. FastAPI + SQLite backend (`backend/`), Vue 3 + Vite + TypeScript + Pinia frontend (`frontend/`).

## Commands

```bash
./start.sh                      # dev: venv + pip install, uvicorn --reload on :8000, vite on :5173
                                # HOST=0.0.0.0 ./start.sh to expose the backend

# Backend (from backend/, with venv active)
uvicorn main:app --reload --port 8000
pip install -r requirements-dev.txt
pytest                          # all tests (pytest.ini: testpaths=tests, pythonpath=.)
pytest tests/test_accounts.py::test_name   # single test
python hash_password.py         # generate AUTH_PASSWORD_HASH
python backup.py --backup [file] | --restore file [--db path]

# Frontend (from frontend/)
npm run dev
npm run build                   # vue-tsc -b && vite build (the only type-check; no lint/test setup)

# Docker (UI on :8080, DB in ./data)
docker compose up -d --build
```

Auth env vars are required for any protected endpoint (otherwise 503): copy `.env.example` to `.env` and set `AUTH_USERNAME`, `AUTH_PASSWORD_HASH`, `SESSION_SECRET` (>=16 chars). Swagger UI is at `http://localhost:8000/docs`.

## Architecture

**Backend** (flat modules, run from `backend/` — imports are top-level like `from database import ...`, not a package):
- `main.py` runs `migrations.run_migrations()` at import time, mounts every router under `Depends(auth.require_auth)` (only `/api/auth/*` and `/api/health` are public), and starts the daily scheduler jobs in the lifespan.
- `migrations.py`: schema evolution is hand-written idempotent `ALTER TABLE` checks on top of `Base.metadata.create_all` — there is no Alembic. New columns need an entry here as well as in `models.py`.
- `auth.py`: stdlib-only single-user HMAC cookie session, PBKDF2 hash, in-memory login rate limit keyed on `x-real-ip` (set by nginx).
- `routers/`: `accounts`, `audit`, `dashboard`, `property` (properties + mortgage parts), `shares` (holdings, live prices, sync), `snapshots`, `export`. `schemas.py` holds all Pydantic models; datetimes serialise as UTC ISO with trailing `Z`.
- `services/`: `prices` (Yahoo fetch, one batched `yf.download` per request), `cache` (in-process 15-min price cache), `fx` (GBP conversion), `landg` (scraping), `snapshot` (daily revaluation of share-holding accounts), `backups`, `scheduler` (`daily_job` with startup catch-up).
- `backup.py` is both a CLI and the JSON format used by `services/backups.py` and `/api/export/backup.json`.

**Key invariants**
- All datetimes are stored as **naive UTC**. Use `utcnow()` from `backend/timeutil.py` — never `datetime.utcnow()`. `utcnow_naive` (also importable from `services/timeutil.py` / `services`) is just an alias of the same single implementation; don't add another.
- Every value change on an account / property / mortgage part writes an audit row (`AuditLog`, `PropertyValueAuditLog`, `MortgagePartAuditLog`). Dashboard history is **reconstructed from these logs** (`dashboard._seed`, `_last_before`), so never mutate a value without a log row. Deletes are soft (`is_active=False`), and value changes on deleted accounts are refused (409) to avoid rewriting history.
- Net worth = sum of active account values + property equity (`(value − active mortgage balances) × ownership%`).
- Auto-snapshots write audit rows noted `[auto-snapshot] ...`; an account is skipped if any holding lacks a price/FX rate. Stale prices fall back to `ShareHolding.last_price*` columns.
- Holdings can be priced in non-GBP currencies: currency is inferred from the ticker in `services/prices.infer_currency` and converted to GBP via `FxSnapshot`.

**Tests** (`backend/tests`): `conftest.py` sets `DB_PATH`/`BACKUP_DIR` to a temp dir and disables the scheduler **before** importing the app — keep that ordering. A session-scoped `TestClient` is shared; see `support.py` for helpers.

**Frontend**: `src/api/client.ts` is the single typed API layer (a `request()` wrapper that redirects to `/login` on 401, `apiErrorMessage()` to unwrap FastAPI `detail`). Pinia stores in `src/stores/` (accounts, audit, mortgage, shares) hold state; views in `src/views/`; components grouped by domain under `src/components/`. The router guard (`router/index.ts`) calls `authApi.check()`. Vite proxies/nginx forwards `/api` to the backend. CSV/backup downloads are plain same-origin anchor links authenticated by the cookie.

**Deployment**: `docker-compose.yml` — backend (DB at `/data/tracker.db`, bind-mounted `./data`; mount directories, never single sqlite files because of WAL/shm) and an nginx frontend on :8080 that waits on the backend healthcheck. Daily jobs are configured via `SNAPSHOT_*` / `BACKUP_*` env vars (see `.env.example`).
- GBP money amounts are floats in SQLite/JSON (unchanged), but arithmetic goes through `services/money.py` (`round_money`, `money_sum`, `money_delta`: Decimal, ROUND_HALF_UP, 2dp) and values are rounded to pence when persisted. Never round share quantities or prices.
