#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# --- 프론트엔드 빌드 ---
if [ -f frontend/package.json ]; then
  cd frontend
  npm ci --prefer-offline
  VITE_API_BASE_URL=https://neomeo.semo3.com npm run build
  cd ..
fi

# --- 백엔드 의존성 + 마이그레이션 ---
if [ -f backend/requirements.txt ]; then
  cd backend
  if [ ! -f .venv/bin/pip ]; then
    python3 -m venv --clear .venv
  fi
  .venv/bin/pip install -r requirements.txt -q
  .venv/bin/alembic upgrade head
  cd ..
fi

# --- PM2 재시작 (neomeo-backend 단일 프로세스) ---
if pm2 list | grep -q neomeo-backend; then
  pm2 reload ecosystem.config.json --update-env
else
  pm2 start ecosystem.config.json
  pm2 save
fi
