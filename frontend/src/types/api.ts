// Types mirroring backend Pydantic schemas (see backend/app/schemas)

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface UserOut {
  id: string;
  email: string | null;
  name: string | null;
  github_handle: string | null;
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
  repo_full_name: string | null;
  repo_id: number | null;
  created_at: string;
  // NOT YET IMPLEMENTED on the backend — see docs/frontend-to-backend-requests.md.
  // Missing/undefined is treated as "not an admin".
  is_admin?: boolean;
}

export interface ProjectOut {
  id: string;
  name: string;
  repo_full_name: string | null;
  repo_id: number | null;
  created_at: string;
}

export interface ProjectCreate {
  name: string;
  repo_full_name?: string;
  repo_id?: number;
  team_id: string;
}

// NOT YET IMPLEMENTED on the backend — see docs/frontend-to-backend-requests.md
export interface ParticipatingTeamOut {
  id: string;
  name: string;
  country: string | null;
  timezone: string;
}

export interface ProjectDocumentOut {
  project_id: string;
  content: string;
  updated_at: string;
}

// NOT YET IMPLEMENTED on the backend — see docs/frontend-to-backend-requests.md
export interface TeamMemberOut {
  user_id: string;
  name: string | null;
  github_handle: string | null;
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

export interface GithubConnectResult {
  project_id: string;
  connected: boolean;
  repo_id: number | null;
  backfill_event_count: number;
}

export interface GithubStatusOut {
  project_id: string;
  connected: boolean;
  last_collected_at: string | null;
  last_error: string | null;
}

// NOT YET IMPLEMENTED on the backend — see docs/frontend-to-backend-requests.md
export interface GithubRepoOut {
  full_name: string;
  owner: string;
  private: boolean;
}

export type CardStatus = "normal" | "no_change";
export type TriggerType = "auto" | "manual";

export interface TimelineCardOut {
  closure_run_id: string;
  team_id: string;
  trigger_type: TriggerType;
  range_start: string;
  range_end: string;
  language: "ko" | "en";
  content: string | null;
  status: CardStatus;
  source_event_urls: string[];
}

export interface BriefingItem {
  title: string;
  url: string;
  reason: string;
}

export interface BriefingOut {
  project_id: string;
  user_id: string;
  generated_at: string;
  needs_my_response: BriefingItem[];
  affects_my_work: BriefingItem[];
  team_progress_summary: string | null;
}

export interface SeedResponse {
  project_id: string;
  team_ids: string[];
  raw_event_count: number;
  message: string;
}
