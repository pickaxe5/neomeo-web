from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_team_leader
from app.models.team import Team, TeamMembership, TeamRole
from app.models.user import User
from app.schemas.team import TeamCreate, TeamOut, TeamUpdate

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Team:
    """O-002 지원 API. 타임존·업무시간 자동 감지·기본값 채우기는 FE 책임이고,
    백엔드는 확인된 값을 그대로 저장한다. 생성자는 자동으로 팀장이 된다."""
    team = Team(**payload.model_dump())
    db.add(team)
    db.flush()

    db.add(TeamMembership(user_id=current_user.id, team_id=team.id, role=TeamRole.LEADER))
    db.commit()
    db.refresh(team)
    return team


@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: str, db: Session = Depends(get_db)) -> Team:
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "팀을 찾을 수 없습니다.")
    return team


@router.patch("/{team_id}", response_model=TeamOut)
def update_team(
    team_id: str,
    payload: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Team:
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "팀을 찾을 수 없습니다.")
    require_team_leader(db, team_id, current_user)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(team, field, value)
    db.commit()
    db.refresh(team)
    return team
