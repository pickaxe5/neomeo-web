import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.project import Project, ProjectAdmin, ProjectTeam
from app.models.team import Team, TeamMembership
from app.models.user import User
from app.schemas.github import GithubRepoOut
from app.schemas.me import MyProjectOut, MyTeamOut
from app.services import github_client

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
) -> list[MyProjectOut]:
    """C-001: 사용자가 속한 팀이 참여 중인 프로젝트 목록. 프로젝트 참여자 = 참여 팀의
    전체 멤버 원칙(4장)에 따라, 팀 소속만으로 프로젝트 접근 범위가 정해진다."""
    projects = (
        db.query(Project)
        .join(ProjectTeam, ProjectTeam.project_id == Project.id)
        .join(TeamMembership, TeamMembership.team_id == ProjectTeam.team_id)
        .filter(TeamMembership.user_id == current_user.id)
        .distinct()
        .order_by(Project.created_at.desc())
        .all()
    )

    admin_project_ids = {
        project_id
        for (project_id,) in db.query(ProjectAdmin.project_id).filter(
            ProjectAdmin.user_id == current_user.id,
            ProjectAdmin.project_id.in_([p.id for p in projects]),
        )
    }
    return [
        MyProjectOut(
            id=p.id,
            name=p.name,
            created_at=p.created_at,
            is_admin=p.id in admin_project_ids,
        )
        for p in projects
    ]


@router.get("/github/repos", response_model=list[GithubRepoOut])
def list_my_github_repos(current_user: User = Depends(get_current_user)) -> list[GithubRepoOut]:
    """docs/frontend-to-backend-requests.md #1: 사용자 본인의 github_access_token으로
    GitHub API를 대신 호출해 접근 가능한 레포 목록만 내려주는 프록시 엔드포인트.
    GitHub OAuth로 로그인하지 않아 토큰이 없는 사용자는 빈 배열(에러 아님)."""
    if not current_user.github_access_token:
        return []

    with httpx.Client(timeout=10) as client:
        try:
            repos = github_client.list_user_repos(client, current_user.github_access_token)
        except github_client.GithubApiError as exc:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    return [
        GithubRepoOut(full_name=r["full_name"], owner=r["owner"]["login"], private=r["private"])
        for r in repos
    ]
