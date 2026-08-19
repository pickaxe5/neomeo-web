"""D-001: 데모 시드 데이터. D2 목표(가짜 0층 데이터)와 동일한 스키마를 사용해
FE(L-001 타임라인)와 AI(S-004·S-005 요약 생성) 파트가 실제 GitHub 수집 없이도
즉시 개발을 시작할 수 있게 한다.

3개국 팀 + 수일치 타임라인 + 미응답 질문형 코멘트(B-003 시연 필수 조건)를 포함한다.
"""

import random
import uuid
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.closure import ClosureRun, ClosureTrigger
from app.models.github_event import EventType, RawEvent
from app.models.project import Project, ProjectAdmin, ProjectDocument, ProjectRepo, ProjectTeam
from app.models.summary import SummaryCard
from app.models.team import Team, TeamMembership, TeamRole
from app.models.user import User
from app.services.closure_service import build_closure_run

DEMO_GITHUB_HANDLE = "demo-reviewer"
DEMO_PROJECT_NAME = "너머 데모"

TEAM_DEFS = [
    {
        "name": "Seoul Team",
        "country": "KR",
        "timezone": "Asia/Seoul",
        "default_language": "ko",
        "roster": ["kim-dev", "park-fe"],
    },
    {
        "name": "Berlin Team",
        "country": "DE",
        "timezone": "Europe/Berlin",
        "default_language": "en",
        "roster": ["anna-berlin", "felix-be"],
    },
    {
        "name": "San Francisco Team",
        "country": "US",
        "timezone": "America/Los_Angeles",
        "default_language": "en",
        "roster": ["sam-sf", "jordan-ai"],
    },
]

# 오늘 기준 [4일 전, 3일 전, 2일 전, 1일 전] 업무 종료 시각을 경계로 3개의 마감 구간을 만든다.
# "1일 전"까지만 써서, 아직 끝나지 않았을 수 있는 오늘 구간은 포함하지 않는다.
DAY_OFFSETS = [4, 3, 2, 1]


def _work_end_utc(team_timezone: str, work_end: time, day: date) -> datetime:
    local_dt = datetime.combine(day, work_end, tzinfo=ZoneInfo(team_timezone))
    return local_dt.astimezone(timezone.utc)


def _random_time_within(window_start: datetime, window_end: datetime) -> datetime:
    delta_seconds = int((window_end - window_start).total_seconds())
    offset = random.randint(0, max(delta_seconds - 60, 60))
    return window_start + timedelta(seconds=offset)


def _unique_number(used: set[int], low: int, high: int) -> int:
    """(project_id, type, github_id) 유니크 제약과 충돌하지 않도록, 이번 시드 실행 안에서
    중복되지 않는 번호를 뽑는다."""
    while True:
        candidate = random.randint(low, high)
        if candidate not in used:
            used.add(candidate)
            return candidate


def _reset_previous_demo_data(db: Session) -> None:
    """재시드 시 이전 데모 프로젝트/팀/유저를 정리해 중복 생성을 막는다."""
    demo_user = db.query(User).filter(User.github_handle == DEMO_GITHUB_HANDLE).first()
    if demo_user is None:
        return

    admin_rows = db.query(ProjectAdmin).filter(ProjectAdmin.user_id == demo_user.id).all()
    project_ids = {row.project_id for row in admin_rows}
    for project_id in project_ids:
        db.query(RawEvent).filter(RawEvent.project_id == project_id).delete()

        closure_ids = [
            row.id for row in db.query(ClosureRun).filter(ClosureRun.project_id == project_id).all()
        ]
        if closure_ids:
            db.query(SummaryCard).filter(SummaryCard.closure_run_id.in_(closure_ids)).delete(
                synchronize_session=False
            )
        db.query(ClosureRun).filter(ClosureRun.project_id == project_id).delete()
        db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).delete()
        db.query(ProjectTeam).filter(ProjectTeam.project_id == project_id).delete()
        db.query(ProjectAdmin).filter(ProjectAdmin.project_id == project_id).delete()
        # 11번(레포 다중 연결)으로 생긴 project_repos도 지워야 Project 삭제 시 FK 위반이 안 난다.
        db.query(ProjectRepo).filter(ProjectRepo.project_id == project_id).delete()
        db.query(Project).filter(Project.id == project_id).delete()

    team_ids = [m.team_id for m in db.query(TeamMembership).filter(TeamMembership.user_id == demo_user.id).all()]
    db.query(TeamMembership).filter(TeamMembership.user_id == demo_user.id).delete()
    for team_id in team_ids:
        remaining = db.query(TeamMembership).filter(TeamMembership.team_id == team_id).count()
        if remaining == 0:
            db.query(Team).filter(Team.id == team_id).delete()

    db.commit()


def seed_demo_project(db: Session, demo_email: str, demo_password: str) -> dict:
    _reset_previous_demo_data(db)

    demo_user = db.query(User).filter(User.email == demo_email).first()
    if demo_user is None:
        demo_user = User(
            email=demo_email,
            password_hash=hash_password(demo_password),
            name="데모 계정",
            github_handle=DEMO_GITHUB_HANDLE,
            github_id=f"demo-{uuid.uuid4().hex[:8]}",
        )
        db.add(demo_user)
        db.flush()
    else:
        demo_user.password_hash = hash_password(demo_password)
        demo_user.github_handle = DEMO_GITHUB_HANDLE

    teams: list[Team] = []
    for team_def in TEAM_DEFS:
        team = Team(
            name=team_def["name"],
            country=team_def["country"],
            timezone=team_def["timezone"],
            work_start=time(9, 0),
            work_end=time(18, 0),
            default_language=team_def["default_language"],
        )
        db.add(team)
        db.flush()
        teams.append(team)

    # 데모 계정은 서울 팀의 팀장 — 브리핑에서 "내가 답해야 할 것"을 바로 확인할 수 있다.
    db.add(TeamMembership(user_id=demo_user.id, team_id=teams[0].id, role=TeamRole.LEADER))
    db.flush()

    earliest_boundary = _work_end_utc(TEAM_DEFS[0]["timezone"], time(18, 0), date.today() - timedelta(days=DAY_OFFSETS[0]))
    project = Project(
        name=DEMO_PROJECT_NAME,
        created_at=earliest_boundary,
    )
    db.add(project)
    db.flush()

    db.add(
        ProjectRepo(
            project_id=project.id,
            repo_full_name="neomeo-team/neomeo-demo",
            repo_id="000000",
            connected_by_user_id=demo_user.id,
        )
    )
    db.add(ProjectAdmin(project_id=project.id, user_id=demo_user.id))
    for team in teams:
        db.add(ProjectTeam(project_id=project.id, team_id=team.id))
    db.add(
        ProjectDocument(
            project_id=project.id,
            content=(
                "너머(Neomeo)는 팀마다 다른 '하루의 끝'을 하나의 프로젝트 시간축으로 잇는 "
                "비동기 인수인계 레이어입니다. 이 문서는 데모용 프로젝트 컨텍스트입니다."
            ),
        )
    )
    db.flush()

    raw_event_count = 0
    used_numbers = {"pr": set(), "issue": set(), "comment": set()}
    for team, team_def in zip(teams, TEAM_DEFS):
        boundaries = [
            _work_end_utc(team_def["timezone"], time(18, 0), date.today() - timedelta(days=offset))
            for offset in DAY_OFFSETS
        ]
        windows = list(zip(boundaries[:-1], boundaries[1:]))

        for window_index, (window_start, window_end) in enumerate(windows):
            is_last_window = window_index == len(windows) - 1
            events = _build_events_for_window(
                project.id, team, team_def, window_start, window_end, is_last_window, used_numbers
            )
            for event in events:
                db.add(event)
            raw_event_count += len(events)
            db.flush()

            build_closure_run(db, project, team, ClosureTrigger.AUTO, window_start, window_end)

    db.commit()

    return {
        "project_id": project.id,
        "team_ids": [team.id for team in teams],
        "raw_event_count": raw_event_count,
        "demo_user_email": demo_user.email,
    }


def _build_events_for_window(
    project_id: uuid.UUID,
    team: Team,
    team_def: dict,
    window_start: datetime,
    window_end: datetime,
    is_last_window: bool,
    used_numbers: dict[str, set[int]],
) -> list[RawEvent]:
    roster = team_def["roster"]
    events: list[RawEvent] = []
    pr_number = _unique_number(used_numbers["pr"], 100, 999)

    events.append(
        RawEvent(
            project_id=project_id,
            team_id=team.id,
            type=EventType.PR,
            github_id=str(pr_number),
            actor_handle=random.choice(roster),
            title=f"[{team.name}] 기능 작업 PR #{pr_number}",
            body="세부 구현 내용을 담은 PR입니다.",
            url=f"https://github.com/neomeo-team/neomeo-demo/pull/{pr_number}",
            state="merged",
            gh_created_at=_random_time_within(window_start, window_end),
            raw_payload={"number": pr_number, "merged": True},
        )
    )

    issue_number = _unique_number(used_numbers["issue"], 1000, 1999)
    events.append(
        RawEvent(
            project_id=project_id,
            team_id=team.id,
            type=EventType.ISSUE,
            github_id=str(issue_number),
            actor_handle=random.choice(roster),
            title=f"[{team.name}] 이슈 #{issue_number}",
            body="발견된 이슈에 대한 설명입니다.",
            url=f"https://github.com/neomeo-team/neomeo-demo/issues/{issue_number}",
            state="closed",
            gh_created_at=_random_time_within(window_start, window_end),
            raw_payload={"number": issue_number, "state": "closed"},
        )
    )

    commit_sha = uuid.uuid4().hex[:7]
    events.append(
        RawEvent(
            project_id=project_id,
            team_id=team.id,
            type=EventType.COMMIT,
            github_id=commit_sha,
            actor_handle=random.choice(roster),
            title=f"fix: {team.name} 관련 수정",
            body=None,
            url=f"https://github.com/neomeo-team/neomeo-demo/commit/{commit_sha}",
            state=None,
            file_paths=["backend/app/services/example.py", "backend/tests/test_example.py"],
            gh_created_at=_random_time_within(window_start, window_end),
            raw_payload={"sha": commit_sha},
        )
    )

    if is_last_window:
        # B-003 시연 필수 조건: 데모 계정을 향한 미응답 질문형 코멘트를 최신 구간에 배치한다.
        review_comment_id = str(_unique_number(used_numbers["comment"], 5000, 5999))
        events.append(
            RawEvent(
                project_id=project_id,
                team_id=team.id,
                type=EventType.REVIEW_COMMENT,
                github_id=review_comment_id,
                actor_handle=random.choice(roster),
                title=f"[{team.name}] PR #{pr_number} 리뷰 코멘트",
                body=f"@{DEMO_GITHUB_HANDLE} 이 부분 API 응답 형식을 이렇게 바꿔도 될까요? 확인 부탁드립니다.",
                url=f"https://github.com/neomeo-team/neomeo-demo/pull/{pr_number}#discussion_r{review_comment_id}",
                state="open",
                gh_created_at=_random_time_within(window_start, window_end),
                raw_payload={"in_reply_to": None, "mentions": [DEMO_GITHUB_HANDLE]},
            )
        )

    return events
