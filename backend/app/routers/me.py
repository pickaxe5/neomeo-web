from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.project import Project, ProjectTeam
from app.models.team import Team, TeamMembership
from app.models.user import User
from app.schemas.me import MyProjectOut, MyTeamOut

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/teams", response_model=list[MyTeamOut])
def list_my_teams(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[MyTeamOut]:
    """C-001: 글로벌 내비게이션이 프로젝트/팀 전환을 제공하려면 로그인한 사용자가
    속한 팀 목록을 알아야 한다."""
    rows = (
        db.query(Team, TeamMembership.role)
        .join(TeamMembership, TeamMembership.team_id == Team.id)
        .filter(TeamMembership.user_id == current_user.id)
        .all()
    )
    return [
        MyTeamOut(
            id=team.id,
            name=team.name,
            country=team.country,
            timezone=team.timezone,
            work_start=team.work_start,
            work_end=team.work_end,
            default_language=team.default_language,
            role=role,
        )
        for team, role in rows
    ]


@router.get("/projects", response_model=list[MyProjectOut])
def list_my_projects(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[Project]:
    """C-001: 사용자가 속한 팀이 참여 중인 프로젝트 목록. 프로젝트 참여자 = 참여 팀의
    전체 멤버 원칙(4장)에 따라, 팀 소속만으로 프로젝트 접근 범위가 정해진다."""
    return (
        db.query(Project)
        .join(ProjectTeam, ProjectTeam.project_id == Project.id)
        .join(TeamMembership, TeamMembership.team_id == ProjectTeam.team_id)
        .filter(TeamMembership.user_id == current_user.id)
        .distinct()
        .order_by(Project.created_at.desc())
        .all()
    )
