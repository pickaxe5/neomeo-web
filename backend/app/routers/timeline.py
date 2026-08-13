from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_team_leader
from app.models.closure import ClosureRun, ClosureTrigger
from app.models.github_event import RawEvent
from app.models.project import Project
from app.models.summary import SummaryCard
from app.models.team import Team
from app.models.user import User
from app.schemas.timeline import ClosureTriggerRequest, TimelineCardOut
from app.services.closure_service import run_closure

router = APIRouter(prefix="/projects/{project_id}", tags=["timeline"])


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
        source_urls = [
            url
            for (url,) in db.query(RawEvent.url)
            .filter(
                RawEvent.project_id == closure_run.project_id,
                RawEvent.team_id == closure_run.team_id,
                RawEvent.gh_created_at >= closure_run.range_start,
                RawEvent.gh_created_at < closure_run.range_end,
            )
            .all()
        ]
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
                source_event_urls=source_urls,
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
) -> TimelineCardOut:
    """S-002: 야근·조기 작업 시 팀장이 추가 작업 마감을 버튼으로 실행한다. 하루 여러 번 가능."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "프로젝트를 찾을 수 없습니다.")
    team = db.get(Team, payload.team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "팀을 찾을 수 없습니다.")
    require_team_leader(db, payload.team_id, current_user)

    closure_run = run_closure(db, project, team, ClosureTrigger.MANUAL)

    card = (
        db.query(SummaryCard)
        .filter(SummaryCard.closure_run_id == closure_run.id, SummaryCard.language == language)
        .first()
    )
    if card is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"'{language}' 언어 카드가 없습니다.")

    return TimelineCardOut(
        closure_run_id=closure_run.id,
        team_id=closure_run.team_id,
        trigger_type=closure_run.trigger_type,
        range_start=closure_run.range_start,
        range_end=closure_run.range_end,
        language=card.language,
        content=card.content,
        status=card.status,
        source_event_urls=[],
    )
