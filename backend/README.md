# 너머 (Neomeo) 백엔드

크로스 타임존 비동기 인수인계 레이어 — 백엔드. 1단계(스키마·API 계약·가짜 0층 데이터)에 이어
2단계(실 GitHub 수집·10분 자동 마감 워커·시간 시뮬레이션)까지 구현되어 있습니다.

## 빠른 시작

```bash
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- API 문서(Swagger, 팀원과 공유하는 API 계약): http://localhost:8000/docs
- DB: localhost:5432 (user/pass/db = neomeo)

컨테이너가 뜨면 마이그레이션이 자동 적용됩니다(`alembic upgrade head`).

## 데모 데이터로 바로 개발 시작하기 (FE·AI 파트용)

실제 GitHub 연동 없이 타임라인·브리핑을 개발할 수 있도록 가짜 0층 데이터를 제공합니다.

```bash
curl -X POST http://localhost:8000/demo/seed
curl -X POST http://localhost:8000/demo/login   # access_token, refresh_token 발급
curl http://localhost:8000/projects/{project_id}/timeline?language=ko
```

- 3개국 팀(Seoul/Berlin/San Francisco), 팀별 마감 구간(closure_runs) 3개, PR·이슈·커밋·리뷰코멘트 이벤트 포함
- 가장 최근 구간에는 데모 계정(`demo-reviewer`)을 향한 **미응답 질문형 리뷰 코멘트**가 포함되어 있습니다 (B-003 시연용)
- `summary_cards.content`는 이벤트가 있는 구간에서는 `NULL`입니다 — **AI 파트가 S-004·S-005 로직으로 이 값을 채우는 것이 계약**입니다. 이벤트가 없는 구간은 백엔드가 "변동 없음" 텍스트를 이미 채워둡니다.

## 0층 데이터 계약 (AI 파트 필독)

`raw_events` 테이블이 모든 AI 산출물(팀 요약, 개인 브리핑)의 단일 원천입니다. 언어 무관 구조화 데이터이며, 각 이벤트는 `url` 필드에 원본 PR·이슈 링크를 갖고 있어 AI 산출물의 근거 표기(L-004)에 그대로 쓸 수 있습니다.

`closure_runs` 1건 = 카드 1장(`summary_cards`, 언어별). AI 파트는 `summary_cards.content IS NULL AND status = 'normal'`인 행을 찾아, 해당 `closure_run`의 `[range_start, range_end)` 구간에 속한 `raw_events`(같은 `project_id`, `team_id`)를 근거로 `content`를 채우면 됩니다.

## GitHub 실연동 사용법

1. `.env`에 `GITHUB_CLIENT_ID`/`GITHUB_CLIENT_SECRET` 발급받아 채우기 (GitHub OAuth App 콜백 URL을 `GITHUB_OAUTH_CALLBACK_URL`과 동일하게 등록)
2. `/auth/github/login`으로 로그인 (repo 스코프 포함) — 이때 GitHub 액세스 토큰이 `users.github_access_token`에 저장됨
3. `POST /projects/{id}/github/connect` `{"repo_full_name": "owner/repo"}` — 로그인한 유저의 토큰으로 실제 접근 권한을 검증하고, 그 자리에서 직전 3일 소급 수집(G-002)까지 수행
4. 이후 10분마다 워커가 자동으로 새 이벤트를 수집하고, 참여 팀의 로컬 업무 종료 시각이 지나면 자동 마감(S-001)까지 수행

**보안 트레이드오프**: `github_access_token`은 평문 저장합니다. 10일 해커톤 범위에서 KMS/암호화 계층은 과설계로 판단했습니다 — 프로덕션 전환 시 반드시 암호화하거나 GitHub App 방식으로 교체할 것.

**워커 제약**: 10분 폴링은 FastAPI 프로세스 안에서 APScheduler로 돕니다. 단일 uvicorn 워커 프로세스를 전제로 하며, `--workers N`으로 스케일하면 폴링이 N번 중복 실행됩니다 (분산 락 없음, 해커톤 범위 밖).

## 시간 시뮬레이션으로 자동 마감 데모하기 (D-003)

```bash
curl -X POST http://localhost:8000/demo/simulate-time \
  -H "Content-Type: application/json" \
  -d '{"project_id": "...", "simulated_now": "2026-08-12T09:30:00Z"}'
```

다음 폴링 사이클(최대 10분)부터 워커가 실제 시각 대신 이 값을 "지금"으로 취급해, 팀의 로컬 업무 종료 시각을 지났는지 판정합니다. `simulated_now`를 생략하면 해제되어 실제 시각으로 돌아갑니다. 수동 마감(`POST /projects/{id}/close`, S-002 야근 버튼)은 시뮬레이션과 무관하게 항상 실제 시각을 씁니다.

## 내 팀·프로젝트 목록 (C-001 글로벌 내비게이션 지원)

기능 명세서에 별도 ID는 없지만, C-001(글로벌 내비게이션의 "프로젝트 전환")과 재방문 시나리오에
필수적이라 추가했습니다.

- `GET /me/teams` — 로그인한 사용자가 속한 팀 목록 (역할 포함)
- `GET /me/projects` — 사용자가 속한 팀들이 참여 중인 프로젝트 목록
- `PATCH /projects/{id}` — 프로젝트 이름 수정 (C-003). 레포 변경은 실접근 검증이 필요해 `/github/connect`로만 가능

## 폴더 구조

```
app/
  core/       설정, DB, JWT/비밀번호, 인증 의존성
  models/     SQLAlchemy 모델 (0층 raw_events 포함)
  schemas/    Pydantic 요청/응답 스키마
  routers/    API 엔드포인트
  services/   비즈니스 로직 (마감/카드 생성, GitHub 수집)
  worker/     10분 폴링 자동 마감 워커 (S-001)
  seed/       데모 시드 스크립트
alembic/      DB 마이그레이션
```

## 담당 기능 (BE, 기능 명세서 v3 기준)

A-001~003(인증) · O-003·005·006(온보딩) · G-001~006(GitHub 연동) · S-001~003·006(마감/요약) · D-001~003(시연 지원) · C-006(배포)

## 배포 (C-006, 온프레미스)

Render 대신 자체 서버(semo3)에 직접 배포하는 방식으로 변경되었습니다. 배포 파이프라인은 저장소
루트(`main`/`frontend` 브랜치에 있음, 이 브랜치가 `main`에 머지되면 그대로 적용됨)에 이미 구성되어
있고, PM/인프라 담당이 서버 쪽 설정(러너 등록, PM2)을 마쳐뒀습니다. 백엔드 담당은 별도 배포 조작 없이
`main`에 코드를 푸시하기만 하면 됩니다.

- `.github/workflows/deploy.yml` — `main` push 시 서버에 등록된 self-hosted 러너(`semo3`)에서
  `git pull origin main && bash deploy.sh` 실행
- `deploy.sh` — 프론트 빌드, 백엔드는 `.venv`에 `requirements.txt` 설치 후 `alembic upgrade head`로
  마이그레이션 적용, 마지막으로 PM2(`neomeo-backend` 프로세스)를 reload/start
- 서버 접근 권한·PM2 `ecosystem.config.json`(서버에만 존재, 저장소에는 없음)은 PM/인프라 담당 소관

배포 성공 여부는 `/health`가 200을 반환하는지로 확인합니다.

## 이번 단계 범위 밖

- 실제 GitHub 크리덴셜로의 최종 E2E 검증 — 지금까지는 모킹된 GitHub 응답 + 시간 시뮬레이션으로 로직을 검증함. `GITHUB_CLIENT_ID`/`SECRET` 발급 후 위 "GitHub 실연동 사용법"으로 최종 확인 필요

## 마이그레이션

```bash
docker compose exec api alembic revision --autogenerate -m "설명"
docker compose exec api alembic upgrade head
```
