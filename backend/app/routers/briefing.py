from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.i18n import get_lang, t
from app.models.project import Project
from app.models.unanswered import UnansweredItem
from app.models.user import User
from app.schemas.briefing import BriefingOut, ResolveUnansweredItemRequest
from app.services.briefing_service import build_briefing

router = APIRouter(prefix="/projects/{project_id}", tags=["briefing"])


@router.get("/briefing", response_model=BriefingOut)
def get_briefing(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> BriefingOut:
    """기능명세서 7.1: 업무 시작 브리핑, 열람 시점 온디맨드 생성. 1단계(답해야 할 것)는
    미응답 항목(3.3), 2단계(내 작업과 맞물린 변경)는 담당 영역(4.2)을 근거로 조립한다.
    3단계(팀 진행 상황)는 AI가 채우는 summary_cards.content를 참조만 하므로, AI 파트
    연동 전까지는 None으로 내려간다 — 그 부분만 아직 AI 연동 대기 상태다."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("project_not_found", lang))
    return build_briefing(db, project, current_user)


@router.patch("/unanswered-items/{item_id}/resolve", status_code=status.HTTP_204_NO_CONTENT)
def resolve_unanswered_item(
    project_id: str,
    item_id: str,
    payload: ResolveUnansweredItemRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_lang),
) -> None:
    """기능명세서 7.2: 오프라인으로 해결한 미응답 항목을 수동으로 완료(또는 취소) 처리한다.
    GitHub에 실제 답변이 달리면 이 체크 없이도 자동으로 해제된다(3.3) — 이 엔드포인트는
    그걸 놓친 경우를 위한 수동 경로다. manually_resolved=True로 표시해, 이후 활동 재수집이
    이 값을 되돌리지 않게 한다."""
    item = db.get(UnansweredItem, item_id)
    if item is None or str(item.project_id) != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("briefing_item_not_found", lang))
    if item.target_user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, t("briefing_item_forbidden", lang))

    item.resolved = payload.resolved
    item.manually_resolved = True
    item.resolved_at = datetime.now(timezone.utc) if payload.resolved else None
    db.commit()
    return None
