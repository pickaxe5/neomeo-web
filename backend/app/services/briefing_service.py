"""기능명세서 7.1: 업무 시작 브리핑. 3단 우선순위(답해야 할 것 → 내 작업과 맞물린 변경 →
팀 진행 상황) 중 1·2단계는 구조화 사실 데이터(0층)와 미응답 항목(3.3)·담당 영역(4.2)만
있으면 AI 없이도 조립할 수 있다. 3단계(팀 진행 상황)는 AI가 생성하는 summary_cards.content를
그대로 참조만 하며, 아직 채워지지 않았으면(AI 파트 미연동) None으로 둔다."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.closure import ClosureRun
from app.models.github_event import EventType, RawEvent
from app.models.project import Project, ProjectTeam
from app.models.summary import SummaryCard
from app.models.team import Team, TeamMembership
from app.models.unanswered import UnansweredItem
from app.models.user import User
from app.schemas.briefing import BriefingItem, BriefingOut

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


def _team_progress_summary(db: Session, project_id, user: User) -> str | None:
    """가장 최근 마감 카드의 내용을 참고용으로 보여준다. AI가 아직 content를 채우지
    않았으면(NULL) 이 단계는 자연스럽게 비어 있는 채로 반환된다."""
    membership = (
        db.query(TeamMembership)
        .join(ProjectTeam, ProjectTeam.team_id == TeamMembership.team_id)
        .filter(ProjectTeam.project_id == project_id, TeamMembership.user_id == user.id)
        .first()
    )
    if membership is None:
        return None
    team = db.get(Team, membership.team_id)
    language = team.default_language if team else "ko"

    row = (
        db.query(SummaryCard)
        .join(ClosureRun, ClosureRun.id == SummaryCard.closure_run_id)
        .filter(ClosureRun.project_id == project_id, SummaryCard.language == language)
        .order_by(ClosureRun.range_end.desc())
        .first()
    )
    return row.content if row else None


def build_briefing(db: Session, project: Project, user: User) -> BriefingOut:
    since = user.last_briefing_viewed_at or project.created_at

    briefing = BriefingOut(
        project_id=project.id,
        user_id=user.id,
        generated_at=datetime.now(timezone.utc),
        needs_my_response=_needs_my_response(db, project.id, user.id),
        affects_my_work=_affects_my_work(db, project.id, since, user),
        team_progress_summary=_team_progress_summary(db, project.id, user),
    )

    user.last_briefing_viewed_at = briefing.generated_at
    db.commit()
    return briefing
