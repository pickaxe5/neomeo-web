#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

FRONTEND_READY=false
BACKEND_READY=false

# --- 프론트엔드 빌드 ---
if [ -f frontend/package.json ]; then
  cd frontend
  npm ci --prefer-offline
  VITE_API_BASE_URL=https://neomeo-api.semo3.com npm run build
  cd ..
  FRONTEND_READY=true
else
  echo "frontend/package.json 없음 — 프론트엔드 빌드 스킵"
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
  BACKEND_READY=true
else
  echo "backend/requirements.txt 없음 — 백엔드 빌드 스킵"
fi

# --- PM2 재시작 (빌드된 산출물이 하나라도 있을 때만) ---
if [ "$FRONTEND_READY" = false ] && [ "$BACKEND_READY" = false ]; then
  echo "빌드된 서비스 없음 — pm2 스킵"
  exit 0
fi

if [ ! -f ecosystem.config.json ]; then
  echo "ecosystem.config.json 없음 — pm2 스킵"
  exit 0
fi

if pm2 list | grep -q neomeo-frontend; then
  pm2 reload ecosystem.config.json --update-env
else
  pm2 start ecosystem.config.json
  pm2 save
fi
