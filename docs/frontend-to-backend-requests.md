# 프론트 → 백엔드 요청 사항

프론트엔드 작업 중 백엔드 API가 없어서 구현하지 못하고 있는 기능들을 정리합니다.
프론트 코드는 아래 엔드포인트가 없어도 에러 없이 동작하도록(기능만 숨김) 이미 방어적으로 작성해 뒀습니다 —
백엔드가 구현되는 즉시 프론트 쪽 추가 작업 없이 바로 붙습니다.

**1~6번은 백엔드 커밋 `0d803cc`(2026-08-11)로 구현 완료, 프론트도 실제 API에 맞춰 반영·검증했습니다.** 7번만 아직 미구현 상태입니다.

---

## 1. 내 GitHub 레포 목록 조회

**상태**: ✅ 구현 완료 (백엔드 커밋 `0d803cc`, 2026-08-11)

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

- `frontend/src/api/github.ts`의 `fetchMyGithubRepos()`. GitHub 미연동 사용자는 빈 배열이 정상 응답이라 이 경우 드롭다운을 숨기고 기존 수동 입력만 보여줌
- `frontend/src/pages/ProjectPage.tsx`의 `SettingsTab` — 목록이 오면 "GitHub 연동" 카드에 owner별로 그룹핑된 `<select>` 드롭다운이 수동 입력 위에 나타남. 드롭다운에서 고르면 입력창에 값이 채워지고, 기존 수동 입력/연결 버튼은 그대로 유지됨(직접 입력도 계속 가능)

**참고**: GitHub REST API의 `GET /user/repos`는 페이지네이션이 있습니다(기본 30개, 최대 100개/페이지). 레포가 많은 조직 계정을 고려해 전체 페이지를 순회하거나, 최소 100개 이상은 가져오는 걸 권장합니다.

---

## 2. 팀 삭제 / 팀 나가기

**상태**: ✅ 구현 완료 (백엔드 커밋 `0d803cc`, 2026-08-11)

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
- ~~리더가 마지막 1명 남은 리더인 상태에서 나가려고 하면 어떻게 할지~~ → **해결됨**: 마지막 남은 리더는 나갈 수 없도록 막고, 이유가 담긴 메시지와 함께 `400`을 반환하도록 구현됨. 프론트는 그 메시지를 그대로 에러 배너에 표시함
- 성공 시 `204 No Content`

**프론트 쪽 연동 지점**: `frontend/src/api/teams.ts`의 `deleteTeam()` / `leaveTeam()`, `frontend/src/pages/TeamPage.tsx`의 "탈퇴 및 삭제" 카드 — 내 역할(`/me/teams`의 `role`)에 따라 리더에게는 삭제, 멤버에게는 나가기 버튼만 노출.

---

## 3. 프로젝트 삭제

**상태**: ✅ 구현 완료 (백엔드 커밋 `0d803cc`, 2026-08-11)

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

**상태**: ✅ 구현 완료 (백엔드 커밋 `0d803cc`, 2026-08-11)

**배경**: 위 3번(프로젝트 삭제)은 관리자만 가능한 기능이라, 관리자가 아닌 사용자에게는 애초에 "삭제" 버튼 자체를 안 보여줘야 합니다. 팀 쪽은 `GET /me/teams`가 `role`을 내려줘서 프론트가 리더/멤버를 구분할 수 있는데, 프로젝트 쪽 `GET /me/projects`(`MyProjectOut`)에는 관리자 여부를 알 수 있는 필드가 없습니다.

**요청**: 기존 `GET /me/projects` 응답의 각 항목에 `is_admin: boolean` 필드 추가 (요청한 사용자가 `project_admins`에 속하는지 여부).

```json
[
  { "id": "...", "name": "...", "repo_full_name": "...", "repo_id": 123, "created_at": "...", "is_admin": true }
]
```

가능하면 `GET /projects/{id}`(`ProjectOut`)에도 같은 필드를 추가해주면 좋습니다 — 지금은 `/me/projects` 하나로만 판단하고 있지만, 나중에 상세 조회만 하는 화면이 생기면 필요해질 수 있습니다.

**실제로는 `GET /projects/{id}`에도 함께 추가되어 내려옵니다(더 좋음).** 프론트는 별도로 `/me/projects`를 다시 조회하지 않고, 이미 로드해 둔 `GET /projects/{id}` 응답의 `project.is_admin`을 그대로 사용하도록 단순화했습니다.

**프론트 쪽 연동 지점**: `frontend/src/types/api.ts`의 `ProjectOut.is_admin` / `MyProjectOut.is_admin` (필수 boolean으로 반영), `frontend/src/pages/ProjectPage.tsx`의 `SettingsTab`에서 `project.is_admin`으로 판단.

---

## 5. 팀원 목록 조회

**상태**: ✅ 구현 완료 (백엔드 커밋 `0d803cc`, 2026-08-11)

**배경**: 팀 상세 화면에서 현재 팀에 소속된 팀원이 누구인지 볼 수 있어야 합니다. 이름은 이메일이 아니라 **GitHub 닉네임**으로 표시하기로 했습니다.

```
GET /teams/{team_id}/members
Authorization: Bearer <access_token>
```

- 해당 팀의 `team_memberships`를 `users`와 조인해서 반환
- **적용됨**: 팀 소속 멤버만 조회 가능하도록 권한 체크가 들어감 (비멤버는 403)

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

**프론트 쪽 연동 지점**: `frontend/src/api/teams.ts`의 `fetchTeamMembers()`, `frontend/src/pages/TeamPage.tsx`의 "팀원" 카드. 403(비멤버)이면 카드 자체를 조용히 숨김.

---

## 6. 프로젝트의 참여 팀 목록 조회

**상태**: ✅ 구현 완료 (백엔드 커밋 `0d803cc`, 2026-08-11)

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

`project_teams`에 연결된 `teams`를 조인해서 반환하면 됩니다. `TeamOut`을 그대로 재사용해도 무방합니다(그 이상 필드가 와도 프론트에서 무시함). **실제로 `TeamOut` 그대로 반환하도록 구현됨** — 프론트 타입도 `ParticipatingTeamOut = TeamOut`으로 맞춰뒀습니다.

**프론트 쪽 연동 지점**: `frontend/src/api/projects.ts`의 `fetchParticipatingTeams()`, `frontend/src/pages/ProjectPage.tsx`의 설정 탭 "참여 팀" 카드(팀 이름 클릭 시 해당 팀 상세 페이지로 이동). 팀을 새로 추가하면 이 목록도 즉시 다시 불러오도록 되어 있음.

---

## 7. 프로젝트 초대 링크 (팀 초대와 같은 패턴, API는 별도)

**상태**: 미구현 (요청일 2026-08-11)

**배경**: PM과 논의 후 정한 방향 — 팀 관리와 프로젝트 관리 모두 "초대 링크" 방식으로 통일하되, 동작이 다르므로 API는 각각 분리합니다.

- **팀 초대** (기존, 이미 구현됨): 팀 리더가 링크 생성 → 받은 사람이 열면 그 사람 개인이 팀원으로 추가됨 (`POST /teams/{id}/invite-links`, `POST /invite/{token}/accept`)
- **프로젝트 초대** (신규 요청): 프로젝트 관리자가 링크 생성 → 받은 사람이 열면, **그 사람이 리더인 팀 중 하나를 골라서 그 팀 전체가 참여 팀으로 추가됨**. 개인이 아니라 팀 단위로 추가된다는 점이 팀 초대와의 핵심 차이

**요청 엔드포인트 A — 프로젝트 초대 링크 생성**

```
POST /projects/{project_id}/invite-links
Authorization: Bearer <access_token>
```

- 프로젝트 관리자만 가능 (위 3/4번의 `is_admin` 체크와 동일), 아니면 403
- 응답 형식은 팀 쪽 `InviteLinkOut`과 동일한 모양으로 맞춰주면 프론트가 재사용하기 편함:

```json
{ "token": "...", "project_id": "...", "expires_at": "2026-09-10T00:00:00Z" }
```

**요청 엔드포인트 B — 프로젝트 초대 수락**

```
POST /project-invite/{token}/accept
Authorization: Bearer <access_token>
Content-Type: application/json

{ "team_id": "..." }
```

- `team_id`는 **요청한 사용자가 리더인 팀**이어야 함 (아니면 403 — 다른 사람이 리더인 팀을 마음대로 참여시키는 것 방지)
- 해당 팀을 `project_teams`에 추가 (이미 참여 중이면 idempotent하게 처리 — 팀 초대의 `joined` 필드와 같은 패턴)
- 토큰 만료/무효 시 팀 초대와 동일하게 에러 처리

**요청 응답 형식**

```json
{
  "project": { "id": "...", "name": "...", "repo_full_name": "...", "repo_id": 123, "created_at": "..." },
  "team": { "id": "...", "name": "...", "country": "...", "timezone": "...", "work_start": "...", "work_end": "...", "default_language": "ko", "created_at": "..." },
  "added": true
}
```

`project`/`team`은 기존 `ProjectOut`/`TeamOut` 그대로 재사용 가능. `added`는 팀 초대의 `joined`와 같은 역할(이미 참여 중이었으면 `false`).

**프론트 쪽 연동 지점**: `frontend/src/api/projects.ts`의 `createProjectInviteLink()` / `acceptProjectInvite()`, `frontend/src/pages/ProjectPage.tsx` 설정 탭의 "팀 초대" 카드(관리자에게만 노출, `is_admin` 필요 — 4번 항목과 연동), `frontend/src/pages/ProjectInviteAcceptPage.tsx`(새 라우트 `/project-invite/:token` — 로그인 확인 → `/me/teams`에서 리더인 팀만 골라 드롭다운으로 보여주고 선택 후 수락).
