#!/usr/bin/env bash
# 서버에서 실행되는 배포 스크립트.
# 스택 확정 후 빌드 커맨드와 pm2 start 커맨드를 채워주세요.
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# --- 빌드 (스택 확정 후 수정) ---
# 예) Node 백엔드 + Vite 프론트엔드:
#   cd frontend && npm ci && npm run build && cd ..
#   cd backend  && npm ci && cd ..

# --- PM2 재시작 ---
# ecosystem.config.json 이 없으면 최초 1회 생성 필요 (서버에서 직접):
#   pm2 start ecosystem.config.json --env production
#   pm2 save
pm2 restart neomeo-web
