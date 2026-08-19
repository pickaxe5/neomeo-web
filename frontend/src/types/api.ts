// Types mirroring backend Pydantic schemas (see backend/app/schemas)

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface UserOut {
  id: string;
  email: string;
  name: string | null;
  github_handle: string | null;
}

export interface SignupRequest {
  email: string;
  password: string;
  name?: string;
}

export type TeamRole = "leader" | "member";

export interface MyTeamOut {
  id: string;
  name: string;
  country: string | null;
  timezone: string;
  work_start: string;
  work_end: string;
  default_language: "ko" | "en";
  role: TeamRole;
}

export interface TeamOut {
  id: string;
  name: string;
  country: string | null;
  timezone: string;
  work_start: string;
  work_end: string;
  default_language: "ko" | "en";
  created_at: string;
}

export interface TeamCreate {
  name: string;
  country?: string;
  timezone: string;
  work_start?: string;
  work_end?: string;
  default_language?: "ko" | "en";
}

export interface TeamUpdate {
  name?: string;
  country?: string;
  timezone?: string;
  work_start?: string;
  work_end?: string;
  default_language?: "ko" | "en";
}

export interface MyProjectOut {
  id: string;
  name: string;
  created_at: string;
  is_admin: boolean;
}

export interface ProjectOut {
  id: string;
  name: string;
  created_at: string;
  is_admin: boolean;
}

export interface ProjectCreate {
  name: string;
  // 아직 소속 팀이 없는 사용자도 프로젝트를 먼저 만들 수 있도록 선택 입력.
  // 나중에 addParticipatingTeam()으로 팀을 추가하면 된다.
  team_id?: string;
}

// GET /projects/{id}/teams actually returns full TeamOut rows — reuse that type instead.
export type ParticipatingTeamOut = TeamOut;

export interface ProjectDocumentOut {
  project_id: string;
  content: string;
  updated_at: string;
  source_filename?: string | null;
}

export type JobRole = "frontend" | "backend" | "ai" | "design" | "planning" | "custom";

export interface TeamMemberOut {
  user_id: string;
  name: string | null;
  github_handle: string | null;
  role: TeamRole;
  job_role: JobRole | null;
  // job_role이 "custom"일 때만 값이 있다.
  job_role_label: string | null;
  assigned_area: string | null;
  assigned_paths: string[] | null;
  assigned_area_confirmed: boolean;
}

export interface MyAssignmentUpdate {
  job_role?: JobRole;
  job_role_label?: string;
  assigned_area?: string;
}

export interface MemberRoleUpdate {
  role: TeamRole;
}

export interface InviteLinkOut {
  token: string;
  team_id: string;
  expires_at: string | null;
}

export interface InviteAcceptResponse {
  team: TeamOut;
  joined: boolean;
}

export interface ProjectInviteLinkOut {
  token: string;
  project_id: string;
  expires_at: string | null;
}

export interface ProjectInviteAcceptResponse {
  project: ProjectOut;
  team: TeamOut;
  added: boolean;
}

export interface GithubConnectResult {
  project_id: string;
  connected: boolean;
  repo_id: string;
  repo_full_name: string;
  backfill_event_count: number;
}

// 프로젝트당 레포를 여러 개 연결할 수 있어 GET .../github/status는 목록을 반환한다.
export interface GithubRepoStatusOut {
  repo_id: string;
  repo_full_name: string;
  last_collected_at: string | null;
  last_error: string | null;
}

export interface GithubRepoOut {
  full_name: string;
  owner: string;
  private: boolean;
}

export type CardStatus = "normal" | "no_change";
export type TriggerType = "auto" | "manual";

export type TimelineEventType = "pull_request" | "issue" | "review_comment" | "commit";

export interface TimelineSourceEvent {
  type: TimelineEventType;
  title: string;
  author: string | null;
  url: string;
  occurred_at: string;
}

export interface TimelineCardOut {
  closure_run_id: string;
  team_id: string;
  trigger_type: TriggerType;
  range_start: string;
  range_end: string;
  language: "ko" | "en";
  content: string | null;
  status: CardStatus;
  // 하위 호환용 — URL만 나열. 새로 붙일 때는 source_events를 쓴다.
  source_event_urls: string[];
  source_events: TimelineSourceEvent[];
}

export interface BriefingItem {
  id: string | null;
  title: string;
  url: string;
  reason: string;
}

export interface TeamProgressCard {
  team_id: string;
  range_start: string;
  range_end: string;
  content: string | null;
}

export interface BriefingOut {
  project_id: string;
  user_id: string;
  generated_at: string;
  needs_my_response: BriefingItem[];
  affects_my_work: BriefingItem[];
  team_progress_summary: TeamProgressCard[];
}

export interface SeedResponse {
  project_id: string;
  team_ids: string[];
  raw_event_count: number;
  message: string;
}
