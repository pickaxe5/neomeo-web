from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_team_leader
from app.core.i18n import get_lang, t
from app.models.closure import ClosureRun, ClosureTrigger
from app.models.github_event import EventType, RawEvent
from app.models.project import Project
from app.models.summary import SummaryCard
from app.models.team import Team
from app.models.user import User
from app.schemas.timeline import ClosureTriggerRequest, TimelineCardOut, TimelineSourceEvent
from app.services.closure_service import run_closure

router = APIRouter(prefix="/projects/{project_id}", tags=["timeline"])

_EVENT_TYPE_LABELS = {
    EventType.PR: "pull_request",
    EventType.ISSUE: "issue",
    EventType.REVIEW_COMMENT: "review_comment",
    EventType.COMMIT: "commit",
}


def _source_events_for_closure(db: Session, closure_run: ClosureRun) -> list[TimelineSourceEvent]:
    """docs/frontend-to-backend-requests.md #13: closure_run 구간에 속한 raw_events를
    발생 순으로 구조화된 로그 항목으로 변환한다."""
    events = (
        db.query(RawEvent)
        .filter(
            RawEvent.project_id == closure_run.project_id,
            RawEvent.team_id == closure_run.team_id,
            RawEvent.gh_created_at >= closure_run.range_start,
            RawEvent.gh_created_at < closure_run.range_end,
        )
        .order_by(RawEvent.gh_created_at.asc())
        .all()
    )
    return [
        TimelineSourceEvent(
            type=_EVENT_TYPE_LABELS.get(event.type, event.type.value),
            title=event.title or event.body or "(제목 없음)",
            author=event.actor_handle,
            url=event.url,
            occurred_at=event.gh_created_at,
        )
        for event in events
    ]


@router.get("/timeline", response_model=list[TimelineCardOut])
def get_timeline(
    project_id: str,
    language: str = "ko",
    db: Session = Depends(get_db),
) -> list[TimelineCardOut]:
    """L-001~004: 참여 팀의 요약 카드를 마감 시각 순으로 정렬해 반환한다.
    카드 상세·시각 병기·배지 표현은 FE 책임이며, 백엔드는 정렬된 데이터와
    근거 이벤트 링크(L-004)만 제공한다."""
    rows = (
        db.query(ClosureRun, SummaryCard)
        .join(SummaryCard, SummaryCard.closure_run_id == ClosureRun.id)
        .filter(ClosureRun.project_id == project_id, SummaryCard.language == language)
        .order_by(ClosureRun.range_end.asc())
        .all()
    )

    cards: list[TimelineCardOut] = []
    for closure_run, summary_card in rows:
        source_events = _source_events_for_closure(db, closure_run)
        cards.append(
            TimelineCardOut(
                closure_run_id=closure_run.id,
                team_id=closure_run.team_id,
                trigger_type=closure_run.trigger_type,
                range_start=closure_run.range_start,
                range_end=closure_run.range_end,
                language=summary_card.language,
                content=summary_card.content,
                status=summary_card.status,
                source_event_urls=list(dict.fromkeys(e.url for e in source_events)),
                source_events=source_events,
            )
        )
    return cards


@router.post("/close", response_model=TimelineCardOut, status_code=status.HTTP_201_CREATED)
def trigger_manual_closure(
    project_id: str,
    payload: ClosureTriggerRequest,
    language: str = "ko",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> TimelineCardOut:
    """S-002: 야근·조기 작업 시 팀장이 추가 작업 마감을 버튼으로 실행한다. 하루 여러 번 가능."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("project_not_found", lang))
    team = db.get(Team, payload.team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("team_not_found", lang))
    require_team_leader(db, payload.team_id, current_user, lang)

    closure_run = run_closure(db, project, team, ClosureTrigger.MANUAL)

    card = (
        db.query(SummaryCard)
        .filter(SummaryCard.closure_run_id == closure_run.id, SummaryCard.language == language)
        .first()
    )
    if card is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("language_card_not_found", lang, language=language))

    source_events = _source_events_for_closure(db, closure_run)
    return TimelineCardOut(
        closure_run_id=closure_run.id,
        team_id=closure_run.team_id,
        trigger_type=closure_run.trigger_type,
        range_start=closure_run.range_start,
        range_end=closure_run.range_end,
        language=card.language,
        content=card.content,
        status=card.status,
        source_event_urls=list(dict.fromkeys(e.url for e in source_events)),
        source_events=source_events,
    )
