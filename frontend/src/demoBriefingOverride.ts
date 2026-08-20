import type { BriefingOut, ParticipatingTeamOut } from "./types/api";

// 발표용 하드코딩 — 이 정확한 프로젝트 ID("너머 데모")의 브리핑 탭에서만 실제 API
// 대신 이 데이터를 보여준다. 다른 프로젝트에는 전혀 영향 없다. 백엔드는 건드리지 않음.
export const DEMO_OVERRIDE_PROJECT_ID = "fc801b30-0930-4f54-a948-71261c8224f4";

export const DEMO_OVERRIDE_TEAMS: ParticipatingTeamOut[] = [
  {
    id: "seoul-team",
    name: "Seoul Team",
    country: "KR",
    timezone: "Asia/Seoul",
    work_start: "09:00",
    work_end: "18:00",
    default_language: "ko",
    created_at: "2026-08-16T00:00:00Z",
  },
  {
    id: "berlin-team",
    name: "Berlin Team",
    country: "DE",
    timezone: "Europe/Berlin",
    work_start: "09:00",
    work_end: "18:00",
    default_language: "en",
    created_at: "2026-08-16T00:00:00Z",
  },
  {
    id: "sf-team",
    name: "San Francisco Team",
    country: "US",
    timezone: "America/Los_Angeles",
    work_start: "09:00",
    work_end: "18:00",
    default_language: "en",
    created_at: "2026-08-16T00:00:00Z",
  },
];

export const DEMO_OVERRIDE_BRIEFING: BriefingOut = {
  project_id: DEMO_OVERRIDE_PROJECT_ID,
  user_id: "demo-user",
  generated_at: "2026-08-20T00:14:00Z",
  needs_my_response: [
    {
      id: "fake-item-1",
      title: "[Seoul Team] 기능 작업 PR #482 리뷰 코멘트",
      url: "https://github.com/neomeo-team/neomeo-demo/pull/482",
      reason: "미응답 @멘션",
    },
  ],
  affects_my_work: [
    {
      id: null,
      title: "fix: Seoul Team 관련 수정",
      url: "https://github.com/neomeo-team/neomeo-demo/commit/a1b2c3d",
      reason: "담당 영역(backend)과 겹치는 변경",
    },
  ],
  // 아래 3건은 실제 배포 서버의 "너머 데모" 타임라인에 AI가 채워둔 진짜 카드 내용을
  // 그대로 옮긴 것 (지어낸 예시 아님). 최신순으로 San Francisco -> Berlin -> San Francisco.
  team_progress_summary: [
    {
      team_id: "sf-team",
      range_start: "2026-08-14T10:00:00Z",
      range_end: "2026-08-15T10:00:00Z",
      content:
        "이번 윈도우 동안 San Francisco Team 관련 작업이 진행되었습니다.\n\n" +
        "- 'backend/app/services/example.py' 및 'backend/tests/test_example.py' 파일에서 San Francisco Team 관련 수정이 이루어졌습니다. (PR #315)\n" +
        "- PR #315이 머지되었습니다. (PR #315)\n" +
        "- 이슈 #1584가 클로즈되었습니다. (Issue #1584)",
    },
    {
      team_id: "berlin-team",
      range_start: "2026-08-15T01:00:00Z",
      range_end: "2026-08-16T01:00:00Z",
      content:
        "이번 윈도우 동안 Berlin 팀의 주요 작업을 완료했습니다.\n\n" +
        "- 버그 수정을 위해 'backend/app/services/example.py'와 'backend/tests/test_example.py' 파일을 업데이트했습니다. (PR #794)\n" +
        "- PR #794가 머지되었습니다. (PR #794)\n" +
        "- API 응답 형식 변경에 대한 논의가 진행되었습니다. (PR #794)\n" +
        "- 이슈 #1283이 종료되었습니다. (Issue #1283)",
    },
    {
      team_id: "sf-team",
      range_start: "2026-08-15T10:00:00Z",
      range_end: "2026-08-16T10:00:00Z",
      content:
        "오늘 San Francisco Team 관련 수정과 기능 작업이 진행되었습니다.\n\n" +
        "- San Francisco Team에 대한 수정이 적용되었습니다. (Commit 000000:8a43b1d)\n" +
        "- 기능 작업이 포함된 PR #597가 머지되었습니다. (PR #597)",
    },
  ],
};
