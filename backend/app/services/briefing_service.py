"""기능명세서 7.1: 업무 시작 브리핑. 3단 우선순위(답해야 할 것 → 내 작업과 맞물린 변경 →
팀 진행 상황) 중 1·2단계는 구조화 사실 데이터(0층)와 미응답 항목(3.3)·담당 영역(4.2)만
있으면 AI 없이도 조립할 수 있다. 3단계(팀 진행 상황)는 마지막으로 본 이후(since) 마감된
모든 팀의 카드 목록이다 — "자는 동안 다른 팀이 뭘 했는지 아침에 전부 본다"가 기획 의도라
가장 최근 1건만 보여주면 안 된다. 카드별로 개인화 서술(personal_progress_summaries)이
있으면 우선 쓰고, 아직 AI가 안 채웠으면(NULL) 팀 공통 카드(summary_cards.content)로 폴백한다."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.closure import ClosureRun
from app.models.github_event import EventType, RawEvent
from app.models.project import Project, ProjectTeam
from app.models.summary import PersonalProgressSummary, SummaryCard
from app.models.team import Team, TeamMembership
from app.models.unanswered import UnansweredItem
from app.models.user import User
from app.schemas.briefing import BriefingItem, BriefingOut, TeamProgressCard

_SIGNAL_REASON = {
    "reviewer_requested": "리뷰 요청",
    "mentioned": "미응답 @멘션",
    "author_reply_needed": "내 게시물에 달린 미응답 코멘트",
}


def _needs_my_response(db: Session, project_id, user_id) -> list[BriefingItem]:
    rows = (
        db.query(UnansweredItem, RawEvent)
        .join(RawEvent, RawEvent.id == UnansweredItem.raw_event_id)
        .filter(
            UnansweredItem.project_id == project_id,
            UnansweredItem.target_user_id == user_id,
            UnansweredItem.resolved.is_(False),
        )
        .order_by(UnansweredItem.detected_at.asc())
        .all()
    )
    return [
        BriefingItem(
            id=item.id,
            title=raw_event.title or raw_event.body or "(제목 없음)",
            url=raw_event.url,
            reason=_SIGNAL_REASON.get(item.signal_type.value, item.signal_type.value),
            why_it_matters=item.why_it_matters,
        )
        for item, raw_event in rows
    ]


def _affects_my_work(db: Session, project_id, since: datetime, user: User) -> list[BriefingItem]:
    """담당 영역이 확정·추론된 팀의 assigned_paths와 파일 경로가 겹치는, 본인 이외의
    커밋을 부재 구간 안에서 찾는다. 담당 영역이 미설정이면 이 단계는 생략한다 (예외 규칙)."""
    memberships = (
        db.query(TeamMembership)
        .join(ProjectTeam, ProjectTeam.team_id == TeamMembership.team_id)
        .filter(ProjectTeam.project_id == project_id, TeamMembership.user_id == user.id)
        .all()
    )
    assigned_dirs: set[str] = set()
    for membership in memberships:
        assigned_dirs.update(membership.assigned_paths or [])
    if not assigned_dirs:
        return []

    events = (
        db.query(RawEvent)
        .filter(
            RawEvent.project_id == project_id,
            RawEvent.type == EventType.COMMIT,
            RawEvent.gh_created_at >= since,
            RawEvent.file_paths.isnot(None),
        )
        .order_by(RawEvent.gh_created_at.desc())
        .all()
    )

    items: list[BriefingItem] = []
    for event in events:
        if event.actor_handle == user.github_handle:
            continue
        matched = {
            path.split("/", 1)[0] if "/" in path else path
            for path in (event.file_paths or [])
        } & assigned_dirs
        if matched:
            items.append(
                BriefingItem(
                    title=event.title or "(제목 없음)",
                    url=event.url,
                    reason=f"담당 영역({', '.join(sorted(matched))})과 겹치는 변경",
                )
            )
    return items


def _team_progress_summary(db: Session, project_id, since: datetime, user: User) -> list[TeamProgressCard]:
    """마지막으로 브리핑을 본 이후(since) 마감된 모든 팀의 카드를 시간순으로 담는다.
    "자는 동안 다른 팀이 뭘 했는지 아침에 전부 본다"는 기획 의도라, 본인 팀으로 좁히거나
    가장 최근 1건만 보여주면 안 된다 — 다른 팀 카드도 내 언어로 개인화해 볼 수 있어야
    하므로(S-005), 팀 필터 없이 프로젝트 전체를 since 기준으로만 거른다."""
    membership = (
        db.query(TeamMembership)
        .join(ProjectTeam, ProjectTeam.team_id == TeamMembership.team_id)
        .filter(ProjectTeam.project_id == project_id, TeamMembership.user_id == user.id)
        .first()
    )
    if membership is None:
        return []
    team = db.get(Team, membership.team_id)
    language = team.default_language if team else "ko"

    rows = (
        db.query(SummaryCard, ClosureRun)
        .join(ClosureRun, ClosureRun.id == SummaryCard.closure_run_id)
        .filter(
            ClosureRun.project_id == project_id,
            ClosureRun.range_end > since,
            SummaryCard.language == language,
        )
        .order_by(ClosureRun.range_end.asc())
        .all()
    )
    if not rows:
        return []

    closure_run_ids = [closure_run.id for _, closure_run in rows]
    personal_by_closure = {
        p.closure_run_id: p.content
        for p in db.query(PersonalProgressSummary).filter(
            PersonalProgressSummary.closure_run_id.in_(closure_run_ids),
            PersonalProgressSummary.user_id == user.id,
        )
    }

    return [
        TeamProgressCard(
            team_id=closure_run.team_id,
            range_start=closure_run.range_start,
            range_end=closure_run.range_end,
            content=personal_by_closure.get(closure_run.id) or card.content,
        )
        for card, closure_run in rows
    ]


def build_briefing(db: Session, project: Project, user: User) -> BriefingOut:
    since = user.last_briefing_viewed_at or project.created_at

    briefing = BriefingOut(
        project_id=project.id,
        user_id=user.id,
        generated_at=datetime.now(timezone.utc),
        needs_my_response=_needs_my_response(db, project.id, user.id),
        affects_my_work=_affects_my_work(db, project.id, since, user),
        team_progress_summary=_team_progress_summary(db, project.id, since, user),
    )

    user.last_briefing_viewed_at = briefing.generated_at
    db.commit()
    return briefing
