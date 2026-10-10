#!/usr/bin/env bash
# Build a clean deployment folder (and .tar.gz) containing only what the NAS needs.
# Usage: ./deploy.sh            -> ./deploy/ and ./deploy.tar.gz
#        OUT=/path ./deploy.sh  -> custom output folder
# Never included: .env / .env.local, data/, databases, backups, venv, node_modules,
# built frontend, tests, caches. The NAS keeps its own .env and ./data.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${OUT:-$ROOT/deploy}"

command -v rsync >/dev/null || { echo "rsync is required"; exit 1; }

# Safety: only ever wipe a folder this script created.
if [ -e "$OUT" ] && [ ! -f "$OUT/.deploy-folder" ]; then
  echo "Refusing to overwrite $OUT (not created by deploy.sh). Remove it or set OUT=…"; exit 1
fi
rm -rf "$OUT"
mkdir -p "$OUT"
touch "$OUT/.deploy-folder"

echo "→ Checking frontend builds…"
(cd "$ROOT/frontend" && npm run build >/dev/null)

echo "→ Copying backend…"
rsync -a \
  --exclude 'venv/' --exclude '__pycache__/' --exclude '*.pyc' --exclude '.pytest_cache/' \
  --exclude 'tests/' --exclude 'pytest.ini' --exclude 'requirements-dev.txt' \
  --exclude '*.db' --exclude '*.db-wal' --exclude '*.db-shm' --exclude 'backup*.json' \
  --exclude '.env' --exclude '.env.local' --exclude '.DS_Store' \
  "$ROOT/backend/" "$OUT/backend/"

echo "→ Copying frontend…"
rsync -a \
  --exclude 'node_modules/' --exclude 'dist/' --exclude '.vscode/' --exclude '.env' --exclude '.env.local' \
  --exclude '.DS_Store' --exclude 'README.md' \
  "$ROOT/frontend/" "$OUT/frontend/"

echo "→ Copying compose + env template…"
cp "$ROOT/docker-compose.yml" "$ROOT/.env.example" "$OUT/"

cat > "$OUT/DEPLOY.txt" <<'TXT'
On the NAS, in the project folder (the one containing .env and data/):

  1. Backup:   docker compose exec backend python backup.py --backup /data/pre-upgrade.json
               cp -a data data-backup-$(date +%Y%m%d)
  2. Copy backend/ and frontend/ from this folder over the existing ones
     (and docker-compose.yml only if you changed it). Do NOT touch .env or data/.
  3. docker compose up -d --build
  4. docker compose logs -f backend      # check for errors
TXT

TAR="$ROOT/deploy.tar.gz"
tar -czf "$TAR" -C "$OUT" --exclude '.deploy-folder' .

echo ""
echo "✓ Deployment folder: $OUT"
echo "✓ Archive:           $TAR ($(du -h "$TAR" | cut -f1))"
echo ""
(cd "$OUT" && find . -maxdepth 2 -not -name '.deploy-folder' | sort | head -40)
