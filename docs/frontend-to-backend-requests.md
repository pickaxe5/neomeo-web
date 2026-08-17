# 프론트 → 백엔드 요청 사항

프론트엔드 작업 중 백엔드 API가 없어서 구현하지 못하고 있는 기능들을 정리합니다.
프론트 코드는 아래 엔드포인트가 없어도 에러 없이 동작하도록(기능만 숨김) 이미 방어적으로 작성해 뒀습니다 —
백엔드가 구현되는 즉시 프론트 쪽 추가 작업 없이 바로 붙습니다.

**1~6번은 백엔드 커밋 `0d803cc`(2026-08-11)로 구현 완료, 7번(프로젝트 초대)도 `edcd723`으로 구현 완료 —
프론트도 전부 실제 API에 맞춰 반영·검증했습니다.**

---

## 🐛 발견한 버그 (8~13번 구현 검증 중 발견, 2026-08-17)

### [블로킹] 팀 없이 만든 프로젝트가 `GET /me/projects`에 안 뜸

**재현**: `POST /projects`에 `team_id`를 안 넣고(8번) 프로젝트를 만들면 정상적으로 생성되고
`is_admin: true`로 응답도 오는데(직접 `GET /projects/{id}`로 조회해도 잘 나옴), 그 직후
`GET /me/projects`를 호출하면 방금 만든 프로젝트가 목록에 없습니다. 로컬 재현:

```
POST /projects {"name":"OrphanProject"}  →  {"id":"5b14...","is_admin":true, ...}
GET /me/projects  →  방금 만든 프로젝트가 빠진 채로 응답
```

**원인**: `app/routers/me.py`의 `list_my_projects`가 `Project` → `ProjectTeam` → `TeamMembership`
조인으로만 "내 프로젝트"를 찾습니다 — "내가 속한 팀이 참여 중인 프로젝트"만 세는 원래 로직인데,
8번 항목으로 팀 없이 만든 프로젝트는 애초에 `ProjectTeam` row가 없으니 이 조인에 절대 안 걸립니다.
결과적으로 만든 사람 본인에게조차 "내 프로젝트" 목록에서 안 보이는 상태가 됩니다 (URL을 직접
알면 `/projects/{id}`로는 들어가지지만, 대시보드에서 찾을 방법이 없음).

**제안하는 수정**: `list_my_projects`에서 "팀 참여 기반"에 더해 "내가 `project_admins`에 속한
프로젝트"도 합집합으로 포함해주세요 (`UNION` 또는 `OR` 조건). 프로젝트 생성자는 항상
`project_admins`에 들어가니(O-003), 이렇게 하면 8번 항목이 실사용 가능해집니다.

**영향**: 8번 항목(팀 없이 프로젝트 먼저 만들기) 자체가 사실상 못 쓰는 상태입니다 — 만들어도
대시보드에 안 보이니 사용자 입장에서는 사라진 것처럼 느껴집니다.

**추가로 확인된 더 넓은 범위**: 8번(팀 없이 생성)만의 문제가 아닙니다. 참여 팀이 이미 여러 개
있는 프로젝트라도, **관리자 본인이 속한 팀 하나만** 12번 항목("참여 팀 내보내기")으로 빠지면
그 즉시 `GET /me/projects`에서 사라집니다 — 다른 두 팀은 여전히 참여 중이고 그 팀 멤버들에게는
프로젝트가 잘 보이는데도요. 로컬 재현: 데모 시드 프로젝트(참여 팀 3개)에서 내가 속한 팀 1개만
`DELETE /projects/{id}/teams/{team_id}`로 내보내면 다른 2개 팀이 남아있어도 `GET /me/projects`가
바로 빈 배열이 됩니다. 즉 관리자가 "내 팀"을 프로젝트에서 빼는 것만으로 스스로 그 프로젝트에
대한 접근 경로를 잃어버릴 수 있어서, 위 제안 수정(`project_admins` 합집합)이 8번뿐 아니라
12번의 실사용성에도 필요합니다.

### [블로킹] `POST /demo/seed` 두 번째 호출부터 500 에러

**재현**: 로컬 Docker(빈 DB)에서 `/demo/seed`를 한 번 호출해 정상 시딩된 뒤, 같은 데모 계정으로
`/demo/seed`를 다시 호출하면(재시딩 — 기존 데모 데이터를 지우고 새로 만드는 로직) 500이 납니다.

**원인**: 로그 상 `sqlalchemy.exc.IntegrityError: ... violates foreign key constraint
"project_repos_project_id_fkey" ... still referenced from table "project_repos"`.
`app/seed/fake_layer0.py`의 재시딩 정리 로직이 기존 데모 프로젝트를 지우기 전에
`RawEvent`/`SummaryCard`/`ClosureRun`/`ProjectDocument`/`ProjectTeam`/`ProjectAdmin`은 지우는데
(11번 항목으로 새로 생긴) `ProjectRepo`는 안 지우고 있어서, `Project` 삭제 시 FK 제약에 걸립니다.
`DELETE /projects/{id}`(3번 항목) 쪽 cascade 삭제 로직에는 이미 `ProjectRepo` 삭제가 들어가 있으니
그거랑 똑같이 맞추면 될 것 같습니다.

**영향**: 로컬 개발·데모 준비 중 재시딩이 필요할 때마다 막힙니다 (DB를 통째로 지우고 처음부터
다시 시딩해야 우회 가능).

### [블로킹] `PATCH /teams/{team_id}/members/me` — job_role 저장 시 500 에러

**재현**: `{"job_role": "frontend", "assigned_area": "..."}`로 PATCH 요청하면 항상 500.

**원인으로 보이는 것**: 로그 상 `sqlalchemy.exc.DataError: invalid input value for enum jobrole: "FRONTEND"`.
Postgres enum(`jobrole`)은 소문자값(`frontend`, `backend`, ...)으로 만들어져 있는데, SQLAlchemy가
Python `JobRole(str, enum.Enum)`을 바인딩할 때 기본적으로 멤버의 `.value`가 아니라 `.name`(대문자)을
DB로 보내는 것으로 보입니다. `Column(Enum(JobRole, values_callable=lambda enum_cls: [e.value for e in
enum_cls]))`처럼 `values_callable`을 지정해주면 해결될 것 같습니다 (또는 동일 문제가 있는 다른 곳도
같이 확인 필요).

**영향**: 기능명세서 4.2(역할·담당 영역 직접 입력) 전체가 막혀 있습니다. 프론트 UI(`TeamPage.tsx`
"내 역할" 카드)는 이미 만들어서 붙여놨는데, 저장을 누르면 이 에러 때문에 실패합니다.

### [경미] `POST /projects` 응답의 `is_admin`이 항상 `false`

프로젝트를 막 생성한 사람은 자동으로 `project_admins`에 들어가는데(정상 동작), `POST /projects`가
바로 돌려주는 응답의 `is_admin` 필드는 `false`로 나옵니다. 이후 `GET /me/projects`나
`GET /projects/{id}`를 다시 부르면 정상적으로 `true`가 나오는 걸 보면, `create_project`가 ORM
객체를 그대로 반환할 때 `is_admin`을 따로 계산해서 채워주지 않는 것 같습니다(`get_project`처럼).

**영향**: 지금 프론트는 프로젝트 생성 직후 `/me/projects`를 다시 불러오는 흐름이라 실사용에 문제는
없지만, 나중에 생성 응답을 바로 쓰는 화면이 생기면 문제가 됩니다.

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

---

## PM 피드백 정리 (2026-08-17)

PM이 전달한 수정사항 중 백엔드 작업이 필요한 항목만 정리합니다. 나머지(타임존/국가 select화,
팀 생성 폼 업무시간 필드 추가, 팀원 GitHub 프로필 사진)는 프론트 단독으로 처리 가능해서 이미
`frontend` 브랜치에 반영했습니다.

**8~13번 전부 백엔드 커밋 `432a368`로 구현 완료, 프론트도 전부 실제 API에 맞춰 반영·검증했습니다
(2026-08-17).**

## 8. 프로젝트 생성 시 팀 선택을 선택사항으로

**배경**: 지금 `POST /projects`는 `team_id`가 필수라서, 아직 소속 팀이 없는 사용자는 프로젝트 자체를
만들 수 없습니다. PM 요청: "먼저 프로젝트를 만들고 나중에 팀을 추가하는 상황도 고려해야 함."

**요청**: `ProjectCreate.team_id`를 optional로 변경. `team_id`가 없으면 `ProjectTeam` row는 만들지 않고
생성자만 `project_admins`에 추가되도록 해주세요. 이후 팀 연결은 이미 있는 `POST /projects/{id}/teams`
(6번 항목, 참여 팀 추가)로 나중에 하면 됩니다 — 별도 새 엔드포인트는 필요 없습니다.

**프론트 쪽 연동 지점**: `frontend/src/pages/DashboardPage.tsx`의 프로젝트 생성 폼 — 팀 선택 `<select>`를
`required` 해제하고, 소속 팀이 없어도 제출 가능하게 바꿀 예정입니다.

---

## 9. 팀원 리더 위임 / 추방

**배경**: 팀장이 다른 멤버에게 리더 권한을 넘기거나, 멤버를 팀에서 내보낼 수 있어야 합니다. 지금은
본인이 스스로 나가는 `POST /teams/{id}/leave`와 팀장이 팀 자체를 지우는 `DELETE /teams/{id}`만 있고,
팀장이 "다른 사람"에게 하는 액션이 없습니다.

**요청 엔드포인트 A — 리더 위임**

```
PATCH /teams/{team_id}/members/{user_id}/role
Authorization: Bearer <access_token>
Content-Type: application/json

{ "role": "leader" }
```

- 요청자가 해당 팀의 리더여야 함 (`require_team_leader`)
- 리더가 스스로를 `member`로 낮추는 경우, 낮춘 후에도 그 팀에 리더가 최소 1명 남아있어야 함
  (팀 나가기의 "마지막 리더는 나갈 수 없음" 제약과 같은 원칙)

**요청 엔드포인트 B — 멤버 추방**

```
DELETE /teams/{team_id}/members/{user_id}
Authorization: Bearer <access_token>
```

- 요청자가 해당 팀의 리더여야 함
- 대상이 요청자 자신이면 400 (자기 자신을 빼는 건 기존 "팀 나가기"로)
- 성공 시 `204 No Content`

**프론트 쪽 연동 지점**: `frontend/src/pages/TeamPage.tsx`의 팀원 목록 — 리더에게만 각 멤버 행에
"리더 위임"/"추방" 버튼이 보이도록 붙일 예정입니다.

---

## 10. 내 역할(job_role)에 직접 입력 옵션

**배경**: 지금 `job_role`은 Postgres enum(`frontend`, `backend`, `ai`, `design`, `planning`)으로 고정돼
있어서, 이 다섯 개에 안 맞는 역할(PM, QA 등)은 표현할 방법이 없습니다.

**요청**: 다음 중 편하신 방향으로 스키마를 확장해주세요.
- (A) enum에 `custom` 같은 값을 추가하고, `custom`일 때만 쓰이는 자유 텍스트 필드(예:
  `job_role_label: str | null`)를 하나 더 추가
- (B) `job_role` 컬럼 자체를 enum 대신 일반 문자열로 완화(제약 없이 자유 입력 허용)

프론트는 (A)라고 가정하고, 기존 `JOB_ROLE_OPTIONS` 드롭다운 마지막에 "기타(직접 입력)"를 추가해서
고르면 그 옆에 텍스트 입력이 나타나는 식으로 구현할 예정입니다. (B)로 가더라도 프론트 쪽은 select를
그냥 텍스트 입력으로 바꾸기만 하면 되니 크게 상관없습니다 — 어느 쪽으로 하실지만 알려주세요.

**프론트 쪽 연동 지점**: `frontend/src/lib/jobRole.ts`의 `JOB_ROLE_OPTIONS`, `frontend/src/pages/TeamPage.tsx`의
"내 역할" 카드.

---

## 11. 프로젝트당 GitHub 레포 다중 연결 + 연결 해제

**배경**: 지금 프로젝트는 `repo_full_name`/`repo_id` 컬럼이 단일 값이라 레포를 1개만 연결할 수
있습니다. PM 요청: "너머 프로젝트에 `neomeo-web`, `neomeo-ai` 레포가 다 연결돼 있어야 프로젝트 파악이
더 잘 되니까, 프로젝트당 여러 레포를 연결할 수 있게 해달라"는 내용입니다. 연결 해제 기능도 없습니다
(연결만 있고 끊기가 없음).

**요청**: `Project` : `repo` 관계를 1:1에서 1:N(또는 N:N)으로 바꾸는 스키마 변경이 필요합니다 — 예를
들어 `project_repos` 같은 조인 테이블을 새로 만들고, 기존 `POST /projects/{id}/github/connect`를
여러 번 호출해 레포를 추가하는 방식으로 확장. 여기에 더해 연결 해제용
`DELETE /projects/{id}/github/repos/{repo_id}` 같은 엔드포인트도 필요합니다.

**참고**: 이건 스키마·수집 워커(G-001~006) 로직에 걸쳐 있는 변경이라 스코프가 꽤 큽니다. 바로
구현하기보다 먼저 설계 방향(1:N vs N:N, 팀별로 보던 흐름을 레포별로도 나눠 보여줄지 등)을 같이
논의하고 진행하는 게 좋을 것 같습니다.

**프론트 쪽 연동 지점**: `frontend/src/pages/ProjectPage.tsx` 설정 탭의 "GitHub 연동" 카드 — 지금의
단일 연결 UI를 레포 목록 + 각 항목 "연결 해제" 버튼으로 바꿀 예정입니다.

---

## 12. 참여 팀을 프로젝트에서 제거 ("팀 내보내기")

**배경**: 지금은 참여 팀 추가(`POST /projects/{id}/teams`, 6번 항목의 GET과 짝)만 있고 제거가
없습니다. PM 요청: "프로젝트 관리자 권한이 있는 경우 팀 내보내기 기능 추가."

**요청 엔드포인트**

```
DELETE /projects/{project_id}/teams/{team_id}
Authorization: Bearer <access_token>
```

- 프로젝트 관리자만 가능 (`require_project_admin`), 아니면 403
- `ProjectTeam` row 제거. 그 팀이 남긴 `closure_runs`/`summary_cards`(과거 타임라인 기록)를 프로젝트에
  남길지는 3번 항목(프로젝트 삭제)과 같은 기준으로 백엔드 판단에 맡깁니다.
- 성공 시 `204 No Content`

**프론트 쪽 연동 지점**: `frontend/src/pages/ProjectPage.tsx` 설정 탭의 "참여 팀" 카드 — 각 팀 옆에
관리자에게만 보이는 "내보내기" 버튼을 추가할 예정입니다.

---

## 13. 타임라인에 변동사항을 로그 형식으로도 노출

**배경**: 지금 타임라인 카드(`TimelineCardOut`)는 AI 요약(`content`)과 근거 URL 목록만
(`source_event_urls: string[]`, URL 문자열만) 내려줍니다. PM 요청은 "요약뿐 아니라 변동사항을
로그(체인지로그) 형식으로도 보여달라"는 내용인데, 정확히 어떤 정보 단위까지 필요한지
(제목/타입/작성자/시각 포함 여부 등)는 저희도 PM과 다시 확인이 필요한 상태입니다 — 아래는 초안입니다.

**요청(초안)**: `source_event_urls: string[]` 대신, 해당 `closure_run` 구간에 속한 `raw_events`를
구조화된 목록으로 내려주면 좋겠습니다.

```json
"source_events": [
  { "type": "pull_request", "title": "...", "author": "...", "url": "...", "occurred_at": "..." },
  { "type": "issue", "title": "...", "author": "...", "url": "...", "occurred_at": "..." }
]
```

기존 `source_event_urls` 필드는 하위 호환을 위해 당분간 같이 내려주셔도 되고, 한 번에 같이
교체하셔도 상관없습니다 — 저희 쪽에서 맞춰서 반영하겠습니다.

**프론트 쪽 연동 지점**: `frontend/src/components/TimelineCard.tsx` — 지금 URL만 나열하는 "sources"
영역을 이벤트 타입 아이콘 + 제목 + 작성자 + 시각이 있는 로그 리스트로 바꿀 예정입니다.
