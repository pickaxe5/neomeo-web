# 프론트 → 백엔드 요청 사항

프론트엔드 작업 중 백엔드 API가 없어서 구현하지 못하고 있는 기능들을 정리합니다.
프론트 코드는 아래 엔드포인트가 없어도 에러 없이 동작하도록(기능만 숨김) 이미 방어적으로 작성해 뒀습니다 —
백엔드가 구현되는 즉시 프론트 쪽 추가 작업 없이 바로 붙습니다.

---

## 1. 내 GitHub 레포 목록 조회

**상태**: 미구현 (요청일 2026-08-11)

**배경**: 프로젝트 설정 화면의 "GitHub 연동"에서 지금은 `owner/repo` 문자열을 직접 타이핑해야 합니다.
사용자 본인 계정과 소속 organization의 레포를 드롭다운으로 골라서 연결할 수 있게 하고 싶은데,
GitHub 액세스 토큰(`users.github_access_token`)이 백엔드에만 있어서 프론트에서 직접 GitHub API를 호출할 수 없습니다.
백엔드가 그 토큰으로 대신 조회해서 목록만 내려주는 프록시 엔드포인트가 필요합니다.

**요청 엔드포인트**

```
GET /me/github/repos
Authorization: Bearer <access_token>
```

- 로그인한 사용자의 `github_access_token`으로 GitHub API(`GET /user/repos` 등, `affiliation=owner,organization_member` 권장)를 호출해서 접근 가능한 레포 목록을 반환
- GitHub 토큰이 없는 사용자(GitHub OAuth로 로그인하지 않은 경우)는 빈 배열 반환 (에러 아님)
- 정렬 기준은 상관없음 — 프론트에서 owner별로 그룹핑해서 표시함

**요청 응답 형식**

```json
[
  { "full_name": "pickaxe5/neomeo-web", "owner": "pickaxe5", "private": false },
  { "full_name": "my-org/some-repo", "owner": "my-org", "private": true }
]
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `full_name` | string | `owner/repo` 형식, `POST /projects/{id}/github/connect`에 그대로 넘길 값 |
| `owner` | string | 개인 계정 또는 organization 이름 (프론트에서 그룹 헤더로 사용) |
| `private` | boolean | 비공개 레포 여부 (프론트에서 "(private)" 표시용) |

**프론트 쪽 연동 지점**

- `frontend/src/api/github.ts`의 `fetchMyGithubRepos()` — 이미 이 엔드포인트를 호출하도록 작성해 뒀고, 404 등 에러가 나면 조용히 드롭다운을 숨기고 기존 수동 입력만 보여줌
- `frontend/src/pages/ProjectPage.tsx`의 `SettingsTab` — 목록이 오면 "GitHub 연동" 카드에 owner별로 그룹핑된 `<select>` 드롭다운이 수동 입력 위에 나타남. 드롭다운에서 고르면 입력창에 값이 채워지고, 기존 수동 입력/연결 버튼은 그대로 유지됨(직접 입력도 계속 가능)

**참고**: GitHub REST API의 `GET /user/repos`는 페이지네이션이 있습니다(기본 30개, 최대 100개/페이지). 레포가 많은 조직 계정을 고려해 전체 페이지를 순회하거나, 최소 100개 이상은 가져오는 걸 권장합니다.

---

## 2. 팀 삭제 / 팀 나가기

**상태**: 미구현 (요청일 2026-08-11)

**배경**: 팀장이 팀을 삭제하거나, 팀원이 스스로 팀에서 빠질 수 있어야 합니다.

**요청 엔드포인트 A — 팀 삭제**

```
DELETE /teams/{team_id}
Authorization: Bearer <access_token>
```

- 팀 리더만 가능 (`require_team_leader`와 동일한 체크, 아니면 403)
- 팀 삭제 시 `team_memberships`, `invite_links`도 함께 정리(cascade) 필요
- 이 팀이 어떤 프로젝트의 참여 팀(`project_teams`)이었다면 그 관계도 함께 제거해야 함. 해당 팀의 `closure_runs`/`summary_cards`(과거 타임라인 기록)를 프로젝트에 남길지, 같이 지울지는 백엔드 판단에 맡김 — 프론트는 성공 응답만 받으면 됨
- 성공 시 `204 No Content`

**요청 엔드포인트 B — 팀 나가기**

```
POST /teams/{team_id}/leave
Authorization: Bearer <access_token>
```

- 로그인한 사용자 본인의 `team_memberships` 행만 제거
- **리더가 마지막 1명 남은 리더인 상태에서 나가려고 하면 어떻게 할지**는 백엔드에서 정책을 정해야 함 (예: 막고 400 에러, 또는 다른 멤버에게 자동으로 리더 위임). 프론트는 에러 메시지를 그대로 사용자에게 보여줄 수 있으니, 막는 경우 이유가 드러나는 메시지를 응답에 담아주면 좋음
- 성공 시 `204 No Content`

**프론트 쪽 연동 지점**: `frontend/src/api/teams.ts`의 `deleteTeam()` / `leaveTeam()`, `frontend/src/pages/TeamPage.tsx`의 "위험 구역" 카드. 두 버튼 모두 이미 만들어져 있고 확인 다이얼로그까지 붙어 있음 — 엔드포인트가 없으면 지금은 클릭 시 에러 배너에 404가 그대로 노출됨.

---

## 3. 프로젝트 삭제

**상태**: 미구현 (요청일 2026-08-11)

**배경**: 프로젝트 관리자가 프로젝트 자체를 삭제할 수 있어야 합니다. (참고: "프로젝트 나가기"는 이 앱에서 프로젝트가 개인이 아니라 팀 단위로 참여하는 구조라 이번 요청에서는 제외했습니다 — 필요해지면 별도로 설계 논의 필요)

```
DELETE /projects/{project_id}
Authorization: Bearer <access_token>
```

- 프로젝트 관리자(`project_admins`)만 가능, 아니면 403
- `project_teams`, `project_admins`, `project_documents`, `github` 연동 정보(`repo_id`, `gh_last_collected_at` 등), `closure_runs`/`summary_cards`, `raw_events`까지 모두 cascade 삭제 필요
- 성공 시 `204 No Content`

**프론트 쪽 연동 지점**: `frontend/src/api/projects.ts`의 `deleteProject()`, `frontend/src/pages/ProjectPage.tsx`의 설정 탭 "삭제" 카드. **이 카드는 아래 4번 항목(`is_admin`)이 `true`로 내려올 때만 화면에 노출됨** — 그 전까지는 관리자를 포함해 아무에게도 안 보임.

---

## 4. `GET /me/projects`에 `is_admin` 필드 추가

**상태**: 미구현 (요청일 2026-08-11)

**배경**: 위 3번(프로젝트 삭제)은 관리자만 가능한 기능이라, 관리자가 아닌 사용자에게는 애초에 "삭제" 버튼 자체를 안 보여줘야 합니다. 팀 쪽은 `GET /me/teams`가 `role`을 내려줘서 프론트가 리더/멤버를 구분할 수 있는데, 프로젝트 쪽 `GET /me/projects`(`MyProjectOut`)에는 관리자 여부를 알 수 있는 필드가 없습니다.

**요청**: 기존 `GET /me/projects` 응답의 각 항목에 `is_admin: boolean` 필드 추가 (요청한 사용자가 `project_admins`에 속하는지 여부).

```json
[
  { "id": "...", "name": "...", "repo_full_name": "...", "repo_id": 123, "created_at": "...", "is_admin": true }
]
```

가능하면 `GET /projects/{id}`(`ProjectOut`)에도 같은 필드를 추가해주면 좋습니다 — 지금은 `/me/projects` 하나로만 판단하고 있지만, 나중에 상세 조회만 하는 화면이 생기면 필요해질 수 있습니다.

**프론트 쪽 연동 지점**: `frontend/src/types/api.ts`의 `MyProjectOut.is_admin` (이미 optional 필드로 타입 선언해 둠, 값이 없으면 "관리자 아님"으로 안전하게 처리), `frontend/src/pages/ProjectPage.tsx`의 `SettingsTab`에서 `fetchMyProjects()` 결과로 판단.

---

## 5. 팀원 목록 조회

**상태**: 미구현 (요청일 2026-08-11)

**배경**: 팀 상세 화면에서 현재 팀에 소속된 팀원이 누구인지 볼 수 있어야 합니다. 이름은 이메일이 아니라 **GitHub 닉네임**으로 표시하기로 했습니다.

```
GET /teams/{team_id}/members
Authorization: Bearer <access_token>
```

- 해당 팀의 `team_memberships`를 `users`와 조인해서 반환
- 팀에 소속된 사람만 조회 가능하도록(비멤버가 다른 팀 멤버 명단을 보지 못하게) 권한 체크를 넣는 게 안전할 것 같음 — 다만 필수는 아니고 백엔드 판단에 맡김

**요청 응답 형식**

```json
[
  { "user_id": "...", "name": "홍길동", "github_handle": "hong-dev", "role": "leader" },
  { "user_id": "...", "name": null, "github_handle": null, "role": "member" }
]
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `user_id` | string | |
| `name` | string \| null | GitHub OAuth로 안 들어왔거나 이름이 없는 경우 null 가능 |
| `github_handle` | string \| null | GitHub OAuth로 로그인하지 않은 사용자는 null — 프론트는 이 경우 `name`으로 대체 표시함 |
| `role` | `"leader" \| "member"` | |

**프론트 쪽 연동 지점**: `frontend/src/api/teams.ts`의 `fetchTeamMembers()`, `frontend/src/pages/TeamPage.tsx`의 "팀원" 카드. 엔드포인트가 없으면 "팀원 목록 기능은 아직 준비 중입니다"라는 안내 문구만 보여주도록 이미 처리해 둠.

---

## 6. 프로젝트의 참여 팀 목록 조회

**상태**: 미구현 (요청일 2026-08-11)

**배경**: 프로젝트 설정 화면에서 지금 이 프로젝트에 어떤 팀들이 참여 중인지 볼 수 있어야 합니다. 지금은 "참여 팀 추가"(`POST /projects/{id}/teams`)만 있고 조회는 없습니다.

```
GET /projects/{project_id}/teams
Authorization: Bearer <access_token>
```

같은 경로에 이미 `POST /projects/{id}/teams`(팀 추가)가 있으니, REST 관례대로 GET 메서드만 추가하면 됩니다.

**요청 응답 형식**

```json
[
  { "id": "...", "name": "서울팀", "country": "KR", "timezone": "Asia/Seoul" },
  { "id": "...", "name": "베를린팀", "country": "DE", "timezone": "Europe/Berlin" }
]
```

`project_teams`에 연결된 `teams`를 조인해서 반환하면 됩니다. `TeamOut`을 그대로 재사용해도 무방합니다(그 이상 필드가 와도 프론트에서 무시함).

**프론트 쪽 연동 지점**: `frontend/src/api/projects.ts`의 `fetchParticipatingTeams()`, `frontend/src/pages/ProjectPage.tsx`의 설정 탭 "참여 팀" 카드(팀 이름 클릭 시 해당 팀 상세 페이지로 이동). 팀을 새로 추가하면 이 목록도 즉시 다시 불러오도록 되어 있음. 엔드포인트가 없으면 "참여 팀 목록 기능은 아직 준비 중입니다"라는 안내 문구만 보여줌.
