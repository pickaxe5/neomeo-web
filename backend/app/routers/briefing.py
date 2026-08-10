from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.briefing import BriefingOut

router = APIRouter(prefix="/projects/{project_id}", tags=["briefing"])


@router.get("/briefing", response_model=BriefingOut)
def get_briefing(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BriefingOut:
    """B-001~005: 업무 시작 브리핑, 온디맨드 생성. 3단 우선순위(내가 답해야 할 것 →
    내 작업 영향 변경 → 팀 진행 상황)를 0층 데이터에서 AI가 생성하는 것이 목표다.

    2단계(AI 파트 연동)에서 실제 생성 로직이 들어갈 자리이며, 지금은 빈 브리핑을
    반환하는 스텁이다. 계약: 이 엔드포인트는 project_id + user_id를 받아 BriefingOut을
    반환하면 되고, 내부 구현(0층 조회 → AI 호출)은 자유롭게 교체 가능하다.
    """
    return BriefingOut(
        project_id=project_id,
        user_id=current_user.id,
        generated_at=datetime.now(timezone.utc),
        needs_my_response=[],
        affects_my_work=[],
        team_progress_summary=None,
    )
