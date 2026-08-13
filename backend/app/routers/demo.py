from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.i18n import get_lang, t
from app.core.security import create_access_token, create_refresh_token
from app.models.project import Project
from app.models.user import User
from app.schemas.auth import TokenPair
from app.schemas.demo import SeedResponse, SimulateTimeRequest, SimulateTimeResult
from app.seed.fake_layer0 import seed_demo_project

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/seed", response_model=SeedResponse, status_code=status.HTTP_201_CREATED)
def seed(db: Session = Depends(get_db)) -> SeedResponse:
    """D-001: 데모 시드 데이터 생성. 3개국 팀·수일치 타임라인·미응답 질문형 코멘트를
    포함한 데모 프로젝트를 만든다. 재호출 시 이전 데모 데이터를 정리하고 다시 만든다."""
    result = seed_demo_project(db, settings.demo_account_email, settings.demo_account_password)
    return SeedResponse(
        project_id=result["project_id"],
        team_ids=result["team_ids"],
        raw_event_count=result["raw_event_count"],
        message=f"데모 시드 완료. 로그인: {result['demo_user_email']}",
    )


@router.post("/login", response_model=TokenPair)
def demo_login(db: Session = Depends(get_db), lang: str = Depends(get_lang)) -> TokenPair:
    """D-002: 버튼 하나로 데모 계정에 로그인한다. 먼저 /demo/seed가 실행되어 있어야 한다."""
    user = db.query(User).filter(User.email == settings.demo_account_email).first()
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("demo_account_missing", lang))
    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/simulate-time", response_model=SimulateTimeResult)
def simulate_time(
    payload: SimulateTimeRequest, db: Session = Depends(get_db), lang: str = Depends(get_lang)
) -> SimulateTimeResult:
    """D-003: 기준 시각을 임의로 이동해 자동 마감·브리핑 발생을 재현.

    10분 폴링 워커(S-001)가 다음 폴링 사이클부터 이 값을 "지금"으로 취급해 팀의 업무 종료
    시각을 지났는지 판정한다. simulated_now를 생략하면 시뮬레이션을 해제한다.
    """
    project = db.get(Project, payload.project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, t("project_not_found", lang))

    project.simulated_now = payload.simulated_now
    db.commit()

    return SimulateTimeResult(
        project_id=project.id, simulated_now=project.simulated_now, applied=project.simulated_now is not None
    )
