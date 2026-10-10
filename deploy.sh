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
cp "$ROOT/docker-compose.yml" "$ROOT/docker-compose.ghcr.yml" "$ROOT/.env.example" "$OUT/"

VERSION="$(date +%Y%m%d-%H%M%S)-$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo nogit)"
echo "$VERSION" > "$OUT/VERSION"

# Build route helper: every run gets a unique image tag, so the NAS never reuses an old image.
cat > "$OUT/up.sh" <<'SH'
#!/usr/bin/env sh
# Run from the project folder (next to .env and data/).
set -e
cd "$(dirname "$0")"
APP_VERSION="$(cat VERSION)" docker compose up -d --build
echo "Running version $(cat VERSION)"
SH
chmod +x "$OUT/up.sh"

cat > "$OUT/DEPLOY.txt" <<'TXT'
Run all commands in the project folder on the NAS (the one containing .env and data/).
Always first: docker compose exec backend python backup.py --backup /data/pre-upgrade.json
              cp -a data data-backup-$(date +%Y%m%d)
Never touch .env or data/.

Option A - copy folders and build on the NAS (original way)
  1. Copy backend/, frontend/, docker-compose.yml, VERSION and up.sh from this folder
     over the existing ones.
  2. ./up.sh          (builds images tagged with the contents of VERSION, then starts)
  3. docker compose logs -f backend

Option B - prebuilt images from GHCR (no source needed on the NAS)
  1. Push a tag (git tag v1.2.0 && git push origin v1.2.0) and wait for the Release run.
  2. Private package: sudo docker login ghcr.io -u jesusgsdev   (PAT with read:packages)
  3. Copy docker-compose.ghcr.yml over the project folder, then:
     APP_VERSION=v1.2.0 docker compose -f docker-compose.ghcr.yml up -d
  Switching between A and B is safe: both use the same ./data and .env.
TXT

TAR="$ROOT/deploy.tar.gz"
tar -czf "$TAR" -C "$OUT" --exclude '.deploy-folder' .

echo ""
echo "✓ Deployment folder: $OUT"
echo "✓ Archive:           $TAR ($(du -h "$TAR" | cut -f1))"
echo ""
(cd "$OUT" && find . -maxdepth 2 -not -name '.deploy-folder' | sort | head -40)
