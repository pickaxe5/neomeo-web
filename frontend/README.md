# 너머 (Neomeo) 프론트엔드

backend(FastAPI)의 API 계약에 맞춰 구성한 React + Vite + TypeScript 프론트엔드입니다.

## 스택

- React 18 + TypeScript
- Vite (dev server 포트 **3000**으로 고정)
- React Router
- 순수 CSS (별도 UI 프레임워크 없음)
- `fetch` 기반 API 클라이언트 + JWT access/refresh 자동 갱신

## 실행 방법

### 1. 백엔드 먼저 띄우기

이 프론트는 `http://localhost:8000`의 backend API를 호출합니다. backend 저장소에서:

```bash
cd backend
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- 헬스체크: `curl http://localhost:8000/health` → `{"status":"ok"}`

### 2. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

- http://localhost:3000 에서 접속
- `vite.config.ts`에서 포트를 3000으로 고정해 뒀습니다 — backend `.env`의 `FRONTEND_BASE_URL` 기본값(`http://localhost:3000`)과 CORS·GitHub OAuth 리다이렉트가 이 포트를 전제로 합니다. **포트를 바꾸면 backend `.env`의 `FRONTEND_BASE_URL`도 같이 바꿔야 합니다.**

### 3. 환경 변수

`frontend/.env` (없으면 `.env.example` 복사):

```
VITE_API_BASE_URL=http://localhost:8000
```

backend를 다른 호스트/포트에서 띄운 경우 이 값을 그에 맞게 바꾸면 됩니다.

## 사용 방법

실제 회원가입/깃허브 연동 없이도 바로 확인할 수 있습니다.

### 1. 접속 & 데모 로그인

http://localhost:3000/login 접속 → **"데모 계정으로 체험하기"** 클릭.
내부적으로 `POST /demo/seed` → `POST /demo/login`이 자동 호출되어 3개국(서울·베를린·샌프란시스코) 팀·프로젝트 데이터로 로그인됨 (GitHub 계정 불필요).

### 2. 대시보드에서 둘러보기

로그인 직후 대시보드에 데모용 팀과 프로젝트가 자동으로 나열됨. 프로젝트 카드를 클릭해 상세로 진입.

### 3. 프로젝트 탭 탐색

#### 타임라인 탭

- **언어 선택** (한국어/English) — 드롭다운을 바꾸면 `GET /projects/{id}/timeline?language=ko|en`을 다시 호출해 카드 내용을 해당 언어로 불러옴
- **팀 선택 + "지금 마감하기"** — 팀을 고르고 버튼을 누르면 그 팀을 지금 시점에서 강제로 마감해 새 카드를 하나 생성함(`POST /projects/{id}/close`, 이른바 "야근 버튼"). 팀을 선택해야 버튼이 활성화되고, 해당 팀의 **리더 권한**이 있어야 성공함(리더가 아니면 403)
- **카드 목록** — 최신 카드가 위로 오도록 정렬. 각 카드는 다음을 보여줌:
  - 배지: "자동 마감"(업무 종료 시각이 지나 자동 생성) / "수동 마감"(방금 버튼으로 생성)
  - 기간(범위)
  - 본문: `content`가 아직 없으면 "카드 생성 중입니다..."(AI가 아직 안 채움), 변동사항이 없으면 "변동 없음" 배지
  - 근거 링크(관련 PR/이슈 URL)
- 데모 계정은 모든 데모 팀의 리더 권한을 갖고 있어 "지금 마감하기"가 바로 동작함

#### 설정 탭

상단에 3개 빠른 액션이 한 줄 그리드로 배치되어 있음:

- **GitHub 연동** — `owner/repo` 형식으로 입력 후 "연결" → `POST /projects/{id}/github/connect` 호출. 연결 여부(연결됨/미연결) 배지와 마지막 수집 시각·오류가 함께 표시됨. 실제 동작하려면 백엔드에 GitHub OAuth 설정이 되어 있어야 함(로그인한 사용자의 GitHub 토큰으로 저장소 접근 권한을 검증)
- **참여 팀 추가** — 내가 속한 팀 중 하나를 골라 "추가" → 해당 프로젝트에 참여 팀으로 등록(`POST /projects/{id}/teams`)
- **이름 변경** — 프로젝트 이름을 수정하고 "변경" → `PATCH /projects/{id}`

그 아래 별도 카드로 **기획 문서(AI 컨텍스트)** — 프로젝트 배경/목표를 적어두면 추후 카드 생성 품질에 활용되는 텍스트를 저장(`PUT /projects/{id}/document`)

#### 브리핑 탭

현재 빈 상태로만 표시됨 — 백엔드 `/projects/{id}/briefing`이 항상 빈 값을 반환하는 스텁이라 AI 연동이 붙기 전까지는 실제 데이터가 나오지 않음

### 4. 팀 관리 & 초대

대시보드 → 팀 카드 클릭 → 팀 설정에서 업무시간/타임존 수정, 초대 링크 생성 후 다른 계정에 공유하면 `/invite/:token` 경로에서 합류 처리됨.

## 화면 구성

| 경로 | 설명 |
| --- | --- |
| `/login` | GitHub OAuth · 데모 계정 · 이메일/비밀번호 로그인 |
| `/oauth/callback` | GitHub 로그인 리다이렉트 처리 (access/refresh 토큰 저장) |
| `/` | 대시보드 — 내 팀·프로젝트 목록/생성 |
| `/projects/:id` | 프로젝트 상세 — 타임라인 / 브리핑 / 설정(GitHub 연결·팀 추가·이름 변경·기획 문서) |
| `/teams/:id` | 팀 설정 — 정보 수정(리더 전용), 초대 링크 생성 |
| `/invite/:token` | 초대 링크 수락 |

## 현재 backend 의존 상태 (프론트 관점)

- **데모 로그인**: 정상 동작
- **GitHub OAuth 로그인**: 프론트 코드는 완성되어 있으나, backend `.env`의 `GITHUB_CLIENT_ID`/`GITHUB_CLIENT_SECRET`이 비어 있으면 동작하지 않음. GitHub OAuth App 등록 후 값을 채우면 바로 됨.
- **이메일/비밀번호 로그인**: 화면은 있으나 backend에 회원가입(`/auth/signup`) 엔드포인트가 없어 데모 계정 외에는 사용 불가.
- **브리핑 탭**: backend `/projects/{id}/briefing`이 항상 빈 값을 반환하는 스텁 상태(AI 서비스 연동 대기 중). 프론트는 빈 상태 UI로 처리해 둠.

## 폴더 구조

```
src/
  api/         backend 라우터별 클라이언트 모듈 (auth, me, teams, projects, github, timeline, briefing, demo)
               + JWT 인증/자동 갱신 공통 요청 래퍼(client.ts)
  types/api.ts backend Pydantic 스키마를 미러링한 TS 타입
  context/     인증 상태(AuthContext)
  components/  공용 UI 컴포넌트 (Navbar, TimelineCard, BriefingPanel 등)
  pages/       화면 단위 페이지
```

## 빌드 확인

```bash
npm run build   # tsc -b && vite build
```
