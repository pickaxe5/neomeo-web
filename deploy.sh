#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# --- 프론트엔드 빌드 ---
cd frontend
npm ci --prefer-offline
VITE_API_BASE_URL=https://neomeo-api.semo3.com npm run build
cd ..

# --- 백엔드 의존성 + 마이그레이션 ---
cd backend
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -r requirements.txt -q
.venv/bin/alembic upgrade head
cd ..

# --- PM2 재시작 ---
if pm2 list | grep -q neomeo-frontend; then
  pm2 reload ecosystem.config.json --update-env
else
  pm2 start ecosystem.config.json
  pm2 save
fi
