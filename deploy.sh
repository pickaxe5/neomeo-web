#!/usr/bin/env bash
# 서버(self-hosted runner)에서 실행되는 배포 스크립트.
# 스택 확정 후 빌드 섹션을 채우고, ecosystem.config.json을 서버에 추가하면 자동 배포됩니다.
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# --- 빌드 (스택 확정 후 수정) ---
# 예) Node 백엔드 + Vite 프론트엔드:
#   cd frontend && npm ci && npm run build && cd ..
#   cd backend  && npm ci && cd ..

# --- PM2 재시작 ---
if [ ! -f ecosystem.config.json ]; then
  echo "ecosystem.config.json 없음 — pm2 시작 스킵. 스택 확정 후 서버에 추가하세요."
  exit 0
fi

if pm2 list | grep -q neomeo-web; then
  pm2 reload ecosystem.config.json --update-env
else
  pm2 start ecosystem.config.json
  pm2 save
fi
