from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_team_leader
from app.models.closure import ClosureRun
from app.models.github_event import RawEvent
from app.models.project import ProjectTeam
from app.models.summary import SummaryCard
from app.models.team import InviteLink, Team, TeamMembership, TeamRole
from app.models.user import User
from app.schemas.team import TeamCreate, TeamMemberOut, TeamOut, TeamUpdate

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


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """docs/frontend-to-backend-requests.md #2A: 팀 리더만 가능. team_memberships·invite_links·
    project_teams와, 이 팀 소속 closure_runs/summary_cards까지 함께 정리한다(cascade).
    raw_events는 프로젝트 0층 데이터라 삭제하지 않고 team_id만 비운다(nullable)."""
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "팀을 찾을 수 없습니다.")
    require_team_leader(db, team_id, current_user)

    closure_run_ids = [row[0] for row in db.query(ClosureRun.id).filter(ClosureRun.team_id == team_id).all()]
    if closure_run_ids:
        db.query(SummaryCard).filter(SummaryCard.closure_run_id.in_(closure_run_ids)).delete(
            synchronize_session=False
        )
        db.query(ClosureRun).filter(ClosureRun.team_id == team_id).delete(synchronize_session=False)

    db.query(RawEvent).filter(RawEvent.team_id == team_id).update(
        {"team_id": None}, synchronize_session=False
    )
    db.query(InviteLink).filter(InviteLink.team_id == team_id).delete(synchronize_session=False)
    db.query(ProjectTeam).filter(ProjectTeam.team_id == team_id).delete(synchronize_session=False)
    db.query(TeamMembership).filter(TeamMembership.team_id == team_id).delete(synchronize_session=False)

    db.delete(team)
    db.commit()
    return None


@router.post("/{team_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_team(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """docs/frontend-to-backend-requests.md #2B: 본인의 team_memberships 행만 제거.
    마지막 남은 리더는 나갈 수 없다 — 팀장 위임 기능이 아직 없어 자동 위임 대신 막고 이유를 응답에 담는다."""
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "팀을 찾을 수 없습니다.")

    membership = (
        db.query(TeamMembership)
        .filter(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id)
        .first()
    )
    if membership is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "이 팀의 멤버가 아닙니다.")

    if membership.role == TeamRole.LEADER:
        other_leader_exists = (
            db.query(TeamMembership)
            .filter(
                TeamMembership.team_id == team_id,
                TeamMembership.role == TeamRole.LEADER,
                TeamMembership.user_id != current_user.id,
            )
            .first()
            is not None
        )
        if not other_leader_exists:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "마지막 팀장은 팀을 나갈 수 없습니다. 팀을 삭제하거나 다른 팀원이 먼저 팀장이 되어야 합니다.",
            )

    db.delete(membership)
    db.commit()
    return None


@router.get("/{team_id}/members", response_model=list[TeamMemberOut])
def list_team_members(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TeamMemberOut]:
    """docs/frontend-to-backend-requests.md #5: 팀 소속 멤버만 조회 가능하도록 권한 체크."""
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "팀을 찾을 수 없습니다.")

    requester_membership = (
        db.query(TeamMembership)
        .filter(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id)
        .first()
    )
    if requester_membership is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "팀 멤버만 조회할 수 있습니다.")

    rows = (
        db.query(User, TeamMembership.role)
        .join(TeamMembership, TeamMembership.user_id == User.id)
        .filter(TeamMembership.team_id == team_id)
        .all()
    )
    return [
        TeamMemberOut(user_id=user.id, name=user.name, github_handle=user.github_handle, role=role)
        for user, role in rows
    ]
